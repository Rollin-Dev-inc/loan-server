import io
from datetime import date
from typing import cast

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DBSession
from app.models import Loan

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/loans/export")
def export_loans(db: DBSession, admin: CurrentAdmin) -> StreamingResponse:
    loans = db.scalars(select(Loan).order_by(Loan.borrowed_at.desc())).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Laporan Peminjaman"

    headers = [
        "ID Pinjaman", "Nama Peminjam", "ID Barang", "Kode Barang", 
        "Durasi (Hari)", "Tanggal Pinjam", "Jatuh Tempo", "Total Bayar", 
        "Status Kembali", "Tanggal Kembali", "Dibuat Pada"
    ]
    ws.append(headers)

    for loan in loans:
        ws.append([
            loan.id,
            loan.borrower_name,
            loan.item_id,
            loan.item_code,
            loan.duration_days,
            loan.borrowed_at.isoformat(),
            loan.due_at.isoformat(),
            loan.price_to_pay,
            "Sudah Kembali" if loan.is_returned else "Belum Kembali",
            loan.returned_at.isoformat() if loan.returned_at else "-",
            loan.created_at.isoformat()
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    filename = f"Laporan_Peminjaman_{date.today().isoformat()}.xlsx"
    headers_response = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers_response
    )
