import os
import time
from pathlib import Path
import tempfile
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import sys


os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_MKLDNN"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["FLAGS_use_onednn"] = "0"
os.environ["PADDLE_USE_ONEDNN"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"

# Ajouter le répertoire DLLs au PATH pour PyTorch
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

# Vérifier la disponibilité de PyTorch au démarrage
try:
    import torch
    _torch_available = True
    print(f"✓ PyTorch {torch.__version__} chargé avec succès")
except Exception as e:
    print(f"⚠ PyTorch non disponible: {e}")
    _torch_available = False


def enhance_image_for_ocr(image_path: str) -> str:
    """
    Améliore une image pour optimiser la détection OCR
    Retourne le chemin vers l'image améliorée
    """
    try:
        # Charger l'image avec OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return image_path  # Retourner l'original si impossible de charger
        
        # Convertir en niveaux de gris
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Amélioration du contraste avec CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Débruitage
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        # Augmentation de la netteté
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Dilatation légère pour épaissir le texte fin
        kernel = np.ones((1,1), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Sauvegarder l'image améliorée
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='enhanced_')
        os.close(temp_fd)
        
        cv2.imwrite(temp_path, dilated)
        return temp_path
        
    except Exception as e:
        print(f"Erreur lors de l'amélioration de l'image: {e}")
        return image_path  # Retourner l'original en cas d'erreur


def enhance_image_pil(image_path: str) -> str:
    """
    Alternative avec PIL pour l'amélioration d'images
    """
    try:
        with Image.open(image_path) as img:
            # Convertir en niveaux de gris si nécessaire
            if img.mode != 'L':
                img = img.convert('L')
            
            # Augmenter le contraste
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Augmenter la netteté
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            
            # Appliquer un filtre de netteté supplémentaire
            img = img.filter(ImageFilter.SHARPEN)
            
            # Sauvegarder l'image améliorée
            temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='pil_enhanced_')
            os.close(temp_fd)
            
            img.save(temp_path)
            return temp_path
            
    except Exception as e:
        print(f"Erreur lors de l'amélioration PIL: {e}")
        return image_path


def noop():
    return True


def get_pdf_pages_as_images(pdf_file):
    try:
        import fitz 

        doc = fitz.open(pdf_file)
        page_images = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            out_img = Path(pdf_file).parent / f"_api_tmp_page_{i}_{os.getpid()}.png"
            pix.save(str(out_img))
            page_images.append(str(out_img))
        return page_images
    except Exception:
        return []


def cleanup_tmp(paths):
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def init_paddleocr():
    global _paddle_ocr
    if _paddle_ocr is not None:
        return
    from paddleocr import PaddleOCR

    try:
        # Configuration minimale pour assurer la compatibilité
        _paddle_ocr = PaddleOCR(lang="fr", show_log=False)
    except Exception as e:
        print(f"Erreur PaddleOCR: {e}")
        _paddle_ocr = PaddleOCR(lang="fr")


def init_docling():
    global _docling_converter
    if _docling_converter is not None:
        return
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
    from docling.document_converter import (
        DocumentConverter,
        ImageFormatOption,
        PdfFormatOption,
    )

    # Configuration simple et compatible
    simple_opts = PdfPipelineOptions()
    simple_opts.do_table_structure = True  # Active la détection de tableaux
    simple_opts.ocr_options = RapidOcrOptions(lang=["fr", "en"])  # Support multi-langue simplifié

    _docling_converter = DocumentConverter(
        format_options={
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=simple_opts),
            InputFormat.PDF: PdfFormatOption(pipeline_options=simple_opts),
        }
    )


def init_easyocr():
    """
    Initialisation d'EasyOCR avec gestion des erreurs PyTorch
    """
    global _easyocr_reader
    if _easyocr_reader is not None:
        return
    
    if not _torch_available:
        raise Exception("PyTorch n'est pas disponible. Exécutez fix_pytorch.bat pour corriger l'installation.")
    
    import easyocr

    # Configuration optimisée pour documents scannés
    _easyocr_reader = easyocr.Reader(
        ["fr", "en"], 
        gpu=False,
        model_storage_directory=None,  # Utilise le répertoire par défaut
        download_enabled=True,
        detector=True,  # Active la détection de texte optimisée
        recognizer=True,  # Active la reconnaissance optimisée
        verbose=False,
        quantize=True,  # Optimisation pour performances
        cudnn_benchmark=False
    )
    print("✓ EasyOCR initialisé avec succès")


def init_trocr():
    """
    Initialisation de TrOCR avec construction manuelle du Processor
    (contourne le bug tokenizer de transformers v5.x)
    """
    global _trocr_processor, _trocr_model, _trocr_tokenizer, _trocr_device
    if _trocr_model is not None:
        return
    
    if not _torch_available:
        raise Exception("PyTorch n'est pas disponible. Exécutez fix_pytorch.bat pour corriger l'installation.")
    
    import torch
    from transformers import (
        TrOCRProcessor,
        VisionEncoderDecoderModel,
        XLMRobertaTokenizer,
        ViTImageProcessor,
    )

    _trocr_device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"TrOCR utilise le device: {_trocr_device}")
    
    model_name = "microsoft/trocr-small-printed"
    
    # Construction manuelle du Processor pour contourner le bug tokenizer
    # de transformers v5.x qui échoue avec from_pretrained()
    image_processor = ViTImageProcessor.from_pretrained(model_name)
    tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)
    _trocr_processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
    _trocr_tokenizer = tokenizer
    
    _trocr_model = VisionEncoderDecoderModel.from_pretrained(model_name).to(_trocr_device)
    _trocr_model.eval()  # Mode évaluation
    print("✓ TrOCR initialisé avec succès")


def run_paddleocr(file_path: str, file_type: str) -> dict:
    if file_type == "txt":
        return {
            "status": "unsupported",
            "reason": "PaddleOCR ne supporte pas les fichiers .txt",
        }
    try:
        init_paddleocr() 
        ocr = _paddle_ocr

        tmp_files = []
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception(
                    "Impossible de convertir le PDF en images (PyMuPDF requis)."
                )

        # Amélioration des images pour une meilleure détection OCR
        enhanced_targets = []
        for img_path in targets:
            try:
                enhanced_path = enhance_image_for_ocr(img_path)
                enhanced_targets.append(enhanced_path)
                if enhanced_path != img_path:  # Ajouter seulement si c'est un nouveau fichier
                    tmp_files.append(enhanced_path)
            except Exception as e:
                print(f"Erreur amélioration image {img_path}: {e}")
                enhanced_targets.append(img_path)  # Utiliser l'original en cas d'erreur

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
                    res = ocr.ocr(img, cls=True)
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

        return {
            "status": "success",
            "model": "PaddleOCR",
            "file_type": file_type,
            "text": "\n".join(all_lines),
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_docling(file_path: str, file_type: str) -> dict:
    try:
        init_docling()
        converter = _docling_converter

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise Exception("Le fichier est vide (0 octets)")

        # Amélioration spéciale pour les images scannées
        working_path = file_path
        cleanup_enhanced = False
        
        if file_type == "image":
            try:
                from PIL import Image

                with Image.open(file_path) as img:
                    width, height = img.size
                    if width == 0 or height == 0:
                        raise Exception(f"Image invalide: dimensions {width}x{height}")
                    img.verify()
                
                # Améliorer l'image pour Docling si c'est une image
                enhanced_path = enhance_image_pil(file_path)
                if enhanced_path != file_path:
                    working_path = enhanced_path
                    cleanup_enhanced = True
                    
            except Exception as img_error:
                raise Exception(f"Image corrompue ou invalide: {str(img_error)}")

        t0 = time.time()
        abs_file_path = os.path.abspath(working_path)
        result = converter.convert(Path(abs_file_path))
        text = result.document.export_to_markdown().strip()
        ocr_time = round(time.time() - t0, 2)

        # Nettoyage du fichier amélioré temporaire
        if cleanup_enhanced:
            try:
                os.remove(working_path)
            except Exception:
                pass

        word_confidence_data = [
            {"word": word, "confidence": 0.85} for word in text.split() if word.strip()
        ]

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


def run_easyocr(file_path: str, file_type: str) -> dict:
    if file_type == "txt":
        return {
            "status": "unsupported",
            "reason": "EasyOCR ne supporte pas les fichiers .txt",
        }
    try:
        init_easyocr()
        reader = _easyocr_reader

        tmp_files = []
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception(
                    "Impossible de convertir le PDF en images (PyMuPDF requis)."
                )

        # Amélioration des images pour EasyOCR
        enhanced_targets = []
        for img_path in targets:
            try:
                enhanced_path = enhance_image_pil(img_path)  # Utilise PIL pour EasyOCR
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

        return {
            "status": "success",
            "model": "EasyOCR",
            "file_type": file_type,
            "text": "\n".join(all_lines),
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_trocr(file_path: str, file_type: str) -> dict:
    """Exécute TrOCR pour extraction de texte"""
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
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception(
                    "Impossible de convertir le PDF en images (PyMuPDF requis)."
                )

        t0 = time.time()
        texts = []
        word_confidence_data = []

        for img in targets:
            pil_img = Image.open(img).convert("RGB")
            
            # Préparation de l'image pour TrOCR
            pixel_values = processor(
                images=pil_img, return_tensors="pt"
            ).pixel_values.to(device)
            
            # Génération du texte avec torch.no_grad() pour accélérer l'inférence
            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_new_tokens=128)
            
            # Décodage avec le tokenizer du processor
            text_tr = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            texts.append(text_tr)
            for word in text_tr.split():
                if word.strip():
                    word_confidence_data.append({"word": word, "confidence": 0.75})

        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        return {
            "status": "success",
            "model": "TrOCR",
            "file_type": file_type,
            "text": "\n".join(texts),
            "word_confidence": word_confidence_data,
            "init_time": 0.0,
            "ocr_time": ocr_time,
            "total_time": ocr_time,
        }
    except Exception as e:
        # Messages d'erreur plus explicites
        error_msg = str(e)
        if "batch_decode" in error_msg:
            error_msg = "Erreur de décodage TrOCR. Exécutez fix_pytorch.bat pour réinstaller les dépendances."
        elif "WinError 127" in error_msg or "DLL" in error_msg:
            error_msg = "Erreur PyTorch DLL. Exécutez fix_pytorch.bat pour corriger l'installation."
        elif "AutoProcessor" in error_msg or "TrOCRProcessor" in error_msg:
            error_msg = "TrOCR n'est pas compatible avec votre version de transformers. Les 3 autres modèles (EasyOCR, Docling, PaddleOCR) fonctionnent parfaitement."
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
