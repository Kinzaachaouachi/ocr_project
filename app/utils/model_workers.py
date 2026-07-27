import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from .confidence_analyzer import (
    build_word_confidence_from_text,
    estimate_word_confidence,
    refine_word_confidence_list,
)

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_MKLDNN"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["FLAGS_use_onednn"] = "0"
os.environ["PADDLE_USE_ONEDNN"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

MAX_OCR_SIDE = 1800
PDF_DPI_FAST = 120
PDF_DPI_DEFAULT = 150

if sys.platform == "win32":
    venv_path = Path(__file__).parent.parent / "venv"
    dll_paths = [
        venv_path / "Lib" / "site-packages" / "torch" / "lib",
        venv_path / "Scripts",
        venv_path / "Lib" / "site-packages" / "torch" / "bin",
    ]
    for dll_path in dll_paths:
        if dll_path.exists():
            os.add_dll_directory(str(dll_path))

_paddle_ocr = None
_docling_converter = None
_easyocr_reader = None
_trocr_processor = None
_trocr_model = None
_trocr_tokenizer = None
_trocr_device = None
_torch_available = False
_init_locks = {
    "paddleocr": threading.Lock(),
    "docling": threading.Lock(),
    "easyocr": threading.Lock(),
    "trocr": threading.Lock(),
}

try:
    import torch

    _torch_available = True
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except Exception:
        pass
    print(f" PyTorch {torch.__version__} chargé avec succès")
except Exception as e:
    print(f"PyTorch non disponible: {e}")
    _torch_available = False


def resize_image_if_needed(image_path: str, max_side: int = MAX_OCR_SIDE) -> str:
    """Downscale large images — major OCR speedup with little quality loss."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        h, w = img.shape[:2]
        longest = max(h, w)
        if longest <= max_side:
            return image_path
        scale = max_side / float(longest)
        resized = cv2.resize(
            img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )
        temp_fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="resized_")
        os.close(temp_fd)
        cv2.imwrite(temp_path, resized)
        return temp_path
    except Exception as e:
        print(f"Erreur resize image: {e}")
        return image_path


def enhance_image_for_ocr(image_path: str, light: bool = True) -> str:
    """Light preprocess by default (CLAHE + sharpen). Heavy denoise only if light=False."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return image_path

        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        if light:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            out = cv2.filter2D(enhanced, -1, kernel)
        else:
            denoised = cv2.fastNlMeansDenoising(enhanced, h=7)
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            binary = cv2.adaptiveThreshold(
                sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            out = cv2.dilate(binary, np.ones((1, 1), np.uint8), iterations=1)

        temp_fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="enhanced_")
        os.close(temp_fd)
        cv2.imwrite(temp_path, out)
        return temp_path
    except Exception as e:
        print(f"Erreur lors de l'amélioration de l'image: {e}")
        return image_path


def enhance_image_pil(image_path: str, light: bool = True) -> str:
    try:
        with Image.open(image_path) as img:
            if img.mode != "L":
                img = img.convert("L")

            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.35 if light else 1.5)

            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.6 if light else 2.0)

            if not light:
                img = img.filter(ImageFilter.SHARPEN)

            temp_fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="pil_enhanced_")
            os.close(temp_fd)
            img.save(temp_path, optimize=True)
            return temp_path
    except Exception as e:
        print(f"Erreur lors de l'amélioration PIL: {e}")
        return image_path


def noop():
    return True


def get_pdf_pages_as_images(pdf_file, dpi: int = PDF_DPI_DEFAULT):
    try:
        import fitz

        doc = fitz.open(pdf_file)
        page_images = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            out_img = Path(pdf_file).parent / f"_api_tmp_page_{i}_{os.getpid()}.png"
            pix.save(str(out_img))
            page_images.append(str(out_img))
        doc.close()
        return page_images
    except Exception:
        return []


def cleanup_tmp(paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def prepare_shared_ocr_inputs(file_path: str, file_type: str) -> dict:
    """
    One-shot prep shared by all models in extract-all:
    PDF→images (once), downscale large images (once).
    Docling keeps the original PDF when possible (native pipeline is faster).
    """
    cleanup = []

    if file_type == "pdf":
        pages = get_pdf_pages_as_images(file_path, dpi=PDF_DPI_FAST)
        cleanup.extend(pages)
        images = []
        for page in pages:
            resized = resize_image_if_needed(page)
            if resized != page:
                cleanup.append(resized)
            images.append(resized)
        return {
            "images": images,
            "docling_path": file_path,
            "file_type": file_type,
            "cleanup": cleanup,
        }

    if file_type == "image":
        resized = resize_image_if_needed(file_path)
        if resized != file_path:
            cleanup.append(resized)
        return {
            "images": [resized],
            "docling_path": resized,
            "file_type": file_type,
            "cleanup": cleanup,
        }

    return {
        "images": [file_path],
        "docling_path": file_path,
        "file_type": file_type,
        "cleanup": cleanup,
    }


def init_paddleocr():
    global _paddle_ocr
    if _paddle_ocr is not None:
        return
    with _init_locks["paddleocr"]:
        if _paddle_ocr is not None:
            return
        from paddleocr import PaddleOCR

        try:
            _paddle_ocr = PaddleOCR(lang="fr", use_angle_cls=False)
        except TypeError:
            try:
                _paddle_ocr = PaddleOCR(lang="fr", show_log=False, use_angle_cls=False)
            except Exception as e:
                print(f"Erreur PaddleOCR init: {e}")
                _paddle_ocr = PaddleOCR(lang="fr")
        print(" PaddleOCR initialisé avec succès")


def init_docling():
    global _docling_converter
    if _docling_converter is not None:
        return
    with _init_locks["docling"]:
        if _docling_converter is not None:
            return
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
        from docling.document_converter import (
            DocumentConverter,
            ImageFormatOption,
            PdfFormatOption,
        )

        simple_opts = PdfPipelineOptions()
        simple_opts.do_table_structure = False
        simple_opts.ocr_options = RapidOcrOptions(lang=["fr", "en"])

        _docling_converter = DocumentConverter(
            format_options={
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=simple_opts),
                InputFormat.PDF: PdfFormatOption(pipeline_options=simple_opts),
            }
        )
        print(" Docling initialisé avec succès")


def init_easyocr():
    global _easyocr_reader
    if _easyocr_reader is not None:
        return
    with _init_locks["easyocr"]:
        if _easyocr_reader is not None:
            return

        if not _torch_available:
            raise Exception(
                "PyTorch n'est pas disponible. Exécutez fix_pytorch.bat pour corriger l'installation."
            )

        import easyocr

        _easyocr_reader = easyocr.Reader(
            ["fr", "en"],
            gpu=False,
            model_storage_directory=None,
            download_enabled=True,
            detector=True,
            recognizer=True,
            verbose=False,
            quantize=True,
            cudnn_benchmark=False,
        )
        print(" EasyOCR initialisé avec succès")


def init_trocr():
    global _trocr_processor, _trocr_model, _trocr_tokenizer, _trocr_device
    if _trocr_model is not None:
        return
    with _init_locks["trocr"]:
        if _trocr_model is not None:
            return

        if not _torch_available:
            raise Exception(
                "PyTorch n'est pas disponible. Exécutez fix_pytorch.bat pour corriger l'installation."
            )

        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        _trocr_device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"TrOCR utilise le device: {_trocr_device}")

        model_name = "microsoft/trocr-small-printed"
        try:
            from transformers import ViTImageProcessor, XLMRobertaTokenizer

            image_processor = ViTImageProcessor.from_pretrained(model_name)
            tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)
            _trocr_processor = TrOCRProcessor(
                image_processor=image_processor, tokenizer=tokenizer
            )
        except Exception as primary_err:
            err_txt = str(primary_err).lower()
            if "sentencepiece" in err_txt or "no module named 'sentencepiece'" in err_txt:
                raise Exception(
                    "TrOCR nécessite sentencepiece. "
                    "Exécutez: pip install sentencepiece tiktoken"
                ) from primary_err

            try:
                _trocr_processor = TrOCRProcessor.from_pretrained(model_name)
                print(
                    f"TrOCRProcessor.from_pretrained OK (après échec XLM: {type(primary_err).__name__})"
                )
            except Exception as fallback_err:
                raise Exception(
                    f"Impossible d'initialiser TrOCRProcessor "
                    f"(primary={primary_err}; fallback={fallback_err})"
                ) from fallback_err

        _trocr_tokenizer = getattr(_trocr_processor, "tokenizer", None)
        _trocr_model = VisionEncoderDecoderModel.from_pretrained(model_name).to(
            _trocr_device
        )
        _trocr_model.eval()
        print(" TrOCR initialisé avec succès")


def warmup_all_models(models=None):
    """Preload OCR engines so extract-all does not pay cold-start cost."""
    targets = models or list(INIT_FUNCS.keys())
    for name in targets:
        fn = INIT_FUNCS.get(name)
        if not fn:
            continue
        try:
            print(f"⏳ Warmup {name}...")
            t0 = time.time()
            fn()
            print(f"✅ {name} prêt ({time.time() - t0:.1f}s)")
        except Exception as e:
            print(f"⚠️ Warmup {name} échoué: {e}")


def run_paddleocr(
    file_path: str,
    file_type: str,
    *,
    prepared_images=None,
    skip_enhance: bool = False,
) -> dict:
    if file_type == "txt":
        return {
            "status": "unsupported",
            "reason": "PaddleOCR ne supporte pas les fichiers .txt",
        }
    try:
        init_paddleocr()
        ocr = _paddle_ocr

        tmp_files = []

        if prepared_images is not None:
            targets = list(prepared_images)
            if not targets:
                raise Exception("Aucune image préparée pour PaddleOCR.")
        else:
            targets = [file_path]
            if file_type == "pdf":
                targets = get_pdf_pages_as_images(file_path)
                tmp_files = list(targets)
                if not targets:
                    raise Exception(
                        "Impossible de convertir le PDF en images (PyMuPDF requis)."
                    )
            else:
                resized = resize_image_if_needed(file_path)
                if resized != file_path:
                    tmp_files.append(resized)
                targets = [resized]

        if skip_enhance:
            enhanced_targets = targets
        else:
            enhanced_targets = []
            for img_path in targets:
                try:
                    enhanced_path = enhance_image_for_ocr(img_path, light=True)
                    enhanced_targets.append(enhanced_path)
                    if enhanced_path != img_path:
                        tmp_files.append(enhanced_path)
                except Exception as e:
                    print(f"Erreur amélioration image {img_path}: {e}")
                    enhanced_targets.append(img_path)

        t0 = time.time()
        all_lines = []
        word_confidence_data = []

        for img in enhanced_targets:
            try:
                res = ocr.predict(img)
                if res and len(res) > 0 and hasattr(res[0], "keys"):
                    ocr_result = res[0]
                    if "rec_texts" in ocr_result:
                        texts = ocr_result["rec_texts"]
                        scores = ocr_result.get("rec_scores", [0.9] * len(texts))
                        for text, confidence in zip(texts, scores):
                            all_lines.append(str(text))
                            for word in str(text).split():
                                word_confidence_data.append(
                                    {
                                        "word": word,
                                        "confidence": round(float(confidence), 2),
                                    }
                                )
                    else:
                        raise TypeError("Format non reconnu")
                else:
                    raise TypeError("Pas de résultats")
            except (TypeError, AttributeError, KeyError):
                try:
                    res = ocr.ocr(img, cls=False)
                except (AttributeError, TypeError):
                    res = ocr.ocr(img)

                if res and len(res) > 0 and res[0]:
                    sorted_lines = sorted(res[0], key=lambda x: x[0][0][1])
                    prev_y = None
                    for line in sorted_lines:
                        try:
                            text = line[1][0] if isinstance(line[1], tuple) else line[1]
                            confidence = (
                                line[1][1]
                                if isinstance(line[1], tuple) and len(line[1]) > 1
                                else 0.9
                            )
                            y_pos = line[0][0][1]

                            if prev_y is not None and (y_pos - prev_y) > 50:
                                all_lines.append("")

                            all_lines.append(str(text))
                            for word in str(text).split():
                                word_confidence_data.append(
                                    {
                                        "word": word,
                                        "confidence": round(float(confidence), 2),
                                    }
                                )
                            prev_y = y_pos
                        except (IndexError, TypeError, ValueError):
                            continue

        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        full_text = "\n".join(all_lines)
        word_confidence_data = refine_word_confidence_list(
            word_confidence_data, model_id="paddleocr", text=full_text
        )

        return {
            "status": "success",
            "model": "PaddleOCR",
            "file_type": file_type,
            "text": full_text,
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_docling(
    file_path: str,
    file_type: str,
    *,
    prepared_images=None,
    skip_enhance: bool = False,
    docling_path: str = None,
) -> dict:
    try:
        init_docling()
        converter = _docling_converter

        working_path = docling_path or file_path
        cleanup_enhanced = False

        file_size = os.path.getsize(working_path)
        if file_size == 0:
            raise Exception("Le fichier est vide (0 octets)")

        if file_type == "image" and not skip_enhance and prepared_images is None:
            try:
                with Image.open(working_path) as img:
                    width, height = img.size
                    if width == 0 or height == 0:
                        raise Exception(f"Image invalide: dimensions {width}x{height}")
                    img.verify()

                enhanced_path = enhance_image_pil(working_path, light=True)
                if enhanced_path != working_path:
                    working_path = enhanced_path
                    cleanup_enhanced = True
            except Exception as img_error:
                raise Exception(f"Image corrompue ou invalide: {str(img_error)}")
        elif file_type == "image" and prepared_images:
            working_path = docling_path or prepared_images[0]

        t0 = time.time()
        abs_file_path = os.path.abspath(working_path)
        result = converter.convert(Path(abs_file_path))
        text = result.document.export_to_markdown().strip()
        ocr_time = round(time.time() - t0, 2)

        if cleanup_enhanced:
            try:
                os.remove(working_path)
            except Exception:
                pass

        word_confidence_data = build_word_confidence_from_text(text, "docling")

        return {
            "status": "success",
            "model": "Docling",
            "file_type": file_type,
            "text": text,
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        error_msg = str(e)
        if "resize.cpp" in error_msg or "!ssize.empty()" in error_msg:
            error_msg = "Image vide ou corrompue détectée. Veuillez vérifier que l'image est valide."
        return {"status": "error", "error": error_msg}


def run_easyocr(
    file_path: str,
    file_type: str,
    *,
    prepared_images=None,
    skip_enhance: bool = False,
) -> dict:
    if file_type == "txt":
        return {
            "status": "unsupported",
            "reason": "EasyOCR ne supporte pas les fichiers .txt",
        }
    try:
        init_easyocr()
        reader = _easyocr_reader

        tmp_files = []

        if prepared_images is not None:
            targets = list(prepared_images)
            if not targets:
                raise Exception("Aucune image préparée pour EasyOCR.")
        else:
            targets = [file_path]
            if file_type == "pdf":
                targets = get_pdf_pages_as_images(file_path)
                tmp_files = list(targets)
                if not targets:
                    raise Exception(
                        "Impossible de convertir le PDF en images (PyMuPDF requis)."
                    )
            else:
                resized = resize_image_if_needed(file_path)
                if resized != file_path:
                    tmp_files.append(resized)
                targets = [resized]

        if skip_enhance:
            enhanced_targets = targets
        else:
            enhanced_targets = []
            for img_path in targets:
                try:
                    enhanced_path = enhance_image_pil(img_path, light=True)
                    enhanced_targets.append(enhanced_path)
                    if enhanced_path != img_path:
                        tmp_files.append(enhanced_path)
                except Exception as e:
                    print(f"Erreur amélioration image pour EasyOCR {img_path}: {e}")
                    enhanced_targets.append(img_path)

        t0 = time.time()
        all_lines = []
        word_confidence_data = []

        for img in enhanced_targets:
            res = reader.readtext(img)
            if res:
                sorted_lines = sorted(res, key=lambda x: x[0][0][1])
                prev_y = None
                for line in sorted_lines:
                    text = line[1]
                    confidence = line[2]
                    y_pos = line[0][0][1]

                    if prev_y is not None and (y_pos - prev_y) > 50:
                        all_lines.append("")

                    all_lines.append(text)
                    for word in text.split():
                        word_confidence_data.append(
                            {"word": word, "confidence": round(confidence, 2)}
                        )
                    prev_y = y_pos

        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        full_text = "\n".join(all_lines)
        word_confidence_data = refine_word_confidence_list(
            word_confidence_data, model_id="easyocr", text=full_text
        )

        return {
            "status": "success",
            "model": "EasyOCR",
            "file_type": file_type,
            "text": full_text,
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_trocr(
    file_path: str,
    file_type: str,
    *,
    prepared_images=None,
    skip_enhance: bool = False,
) -> dict:
    if file_type == "txt":
        return {
            "status": "unsupported",
            "reason": "TrOCR ne supporte pas les fichiers .txt",
        }
    try:
        init_trocr()
        processor = _trocr_processor
        model = _trocr_model
        device = _trocr_device

        import torch
        from PIL import Image

        tmp_files = []

        if prepared_images is not None:
            targets = list(prepared_images)
            if not targets:
                raise Exception("Aucune image préparée pour TrOCR.")
        else:
            targets = [file_path]
            if file_type == "pdf":
                targets = get_pdf_pages_as_images(file_path)
                tmp_files = list(targets)
                if not targets:
                    raise Exception(
                        "Impossible de convertir le PDF en images (PyMuPDF requis)."
                    )
            else:
                resized = resize_image_if_needed(file_path)
                if resized != file_path:
                    tmp_files.append(resized)
                targets = [resized]

        t0 = time.time()
        texts = []
        word_confidence_data = []

        for img in targets:
            pil_img = Image.open(img).convert("RGB")

            pixel_values = processor(
                images=pil_img, return_tensors="pt"
            ).pixel_values.to(device)

            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_new_tokens=96)

            text_tr = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

            texts.append(text_tr)
            for word in text_tr.split():
                if word.strip():
                    word_confidence_data.append(
                        {
                            "word": word,
                            "confidence": estimate_word_confidence(word, "trocr"),
                        }
                    )

        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        full_text = "\n".join(texts)
        word_confidence_data = refine_word_confidence_list(
            word_confidence_data, model_id="trocr", text=full_text
        )

        return {
            "status": "success",
            "model": "TrOCR",
            "file_type": file_type,
            "text": full_text,
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        error_msg = str(e)
        if "batch_decode" in error_msg:
            error_msg = "Erreur de décodage TrOCR. Vérifiez transformers/torch (pip install -U transformers)."
        elif "WinError 127" in error_msg or "DLL" in error_msg:
            error_msg = "Erreur PyTorch DLL. Exécutez fix_pytorch.bat pour corriger l'installation."
        elif (
            "TrOCRProcessor" in error_msg
            or "AutoProcessor" in error_msg
            or "tokenizer" in error_msg.lower()
        ):
            error_msg = (
                "TrOCR: problème d'initialisation du processor/tokenizer. "
                f"Détail: {e}"
            )
        return {"status": "error", "error": error_msg}


INIT_FUNCS = {
    "paddleocr": init_paddleocr,
    "docling": init_docling,
    "easyocr": init_easyocr,
    "trocr": init_trocr,
}

INFERENCE_FUNCS = {
    "paddleocr": run_paddleocr,
    "docling": run_docling,
    "easyocr": run_easyocr,
    "trocr": run_trocr,
}
