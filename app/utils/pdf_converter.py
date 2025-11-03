import pypdfium2 as pdfium
from PIL import Image

def pdf_page_images_generator(file_path: str, dpi: int = 300):
    """
    A generator that yields one PIL Image per page at the given DPI.

    Args:
        file_path: Path to the PDF file.
        dpi: Desired resolution (default 300 DPI).

    Yields:
        (page_number, PIL.Image) tuples.
    """
    try:
        pdf = pdfium.PdfDocument(file_path)
    except Exception as e:
        # If it's not a PDF, try to open it as an image
        yield 1, Image.open(file_path)
        return # Exit the generator after yielding the image

    # Scale factor: PDF uses 72 DPI base
    scale = dpi / 72

    for i, page in enumerate(pdf):
        pil_image = page.render(scale=int(scale)).to_pil()
        yield i + 1, pil_image  # 1-based page numbers


if __name__ == '__main__':
    file_path = r'C:/Users/Dell/OneDrive/Documents/3PL/sample_documents/3835-22 MULTILINK CO+INV+PL+BL.pdf'
    
    images = []
    for page_num, image in pdf_page_images_generator(file_path, dpi=300):
        # Example action: Save immediately instead of storing in memory
        # image.save(f"page_{page_num}.png")
        images.append(image)
