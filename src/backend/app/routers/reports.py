from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.schemas import PDFReport, MessageResponse
from app.auth import get_current_user, require_admin
from app.database import get_db
import aiosqlite
from pathlib import Path
import os

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports", response_model=list[PDFReport])
async def get_reports(
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of generated PDF reports (admin only)."""
    await require_admin(current_user)
    
    cursor = await db.execute(
        "SELECT id, filename, generated_at FROM pdf_reports ORDER BY generated_at DESC"
    )
    rows = await cursor.fetchall()
    
    return [PDFReport(id=row["id"], filename=row["filename"], generated_at=row["generated_at"]) for row in rows]


@router.post("/reports/generate", response_model=PDFReport)
async def generate_pdf_now(
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Trigger immediate PDF report generation (admin only)."""
    await require_admin(current_user)
    
    from app.pdf_reports import generate_report
    file_path = await generate_report(db)
    
    # Extract filename from path
    filename = Path(file_path).name
    
    return PDFReport(
        id=1,
        filename=filename,
        generated_at=file_path
    )


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Download PDF report."""
    # Allow both admin and viewer to download
    cursor = await db.execute(
        "SELECT file_path, filename FROM pdf_reports WHERE id = ?",
        (report_id,)
    )
    row = await cursor.fetchone()
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    file_path = row["file_path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )
    
    return FileResponse(
        path=file_path,
        filename=row["filename"],
        media_type="application/pdf"
    )
