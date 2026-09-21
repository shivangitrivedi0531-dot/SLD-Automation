import os
import ezdxf
import ezdxf.addons.drawing.matplotlib as ez_mpl
from ezdxf.addons.drawing.config import Configuration


def convert_dxf_to_pdf(dxf_path: str, pdf_path: str) -> None:
    """Convert a DXF drawing file into a vector PDF document.

    Args:
        dxf_path: Absolute or relative path to the input DXF file.
        pdf_path: Absolute or relative path to save the generated vector PDF.
    """
    if not os.path.exists(dxf_path):
        raise FileNotFoundError(f"Input DXF file not found: {dxf_path}")

    # Ensure target output directory exists
    pdf_dir = os.path.dirname(pdf_path)
    if pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)

    # Load DXF document modelspace
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Configure rendering parameters for vector PDF output
    config = Configuration(
        min_lineweight=0.25,
    )

    # Export modelspace directly to vector PDF using matplotlib backend
    ez_mpl.qsave(
        msp,
        pdf_path,
        bg="#FFFFFF",
        config=config,
    )
