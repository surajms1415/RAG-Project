import io
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import pandas as pd
import docx
import pptx
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Add workspace to path
sys.path.insert(0, os.path.abspath("."))

from src.app.core.database import Base, get_db
from src.app.main import create_application


TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    app = create_application()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generates a multi-page valid PDF with text and tables in memory."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Financial Report 2026", author="CFO Office")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Financial Report 2026", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Executive Summary: Revenue grew by 24% year over year.", styles["Normal"]),
        Spacer(1, 12),
    ]

    # Add a table
    table_data = [
        ["Quarter", "Revenue (M$)", "EBITDA (M$)"],
        ["Q1", "120", "34"],
        ["Q2", "145", "42"],
    ]
    t = Table(table_data)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])
    )
    story.append(t)
    doc.build(story)
    return buf.getvalue()


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Generates a valid DOCX with headings, text, and tables."""
    doc = docx.Document()
    doc.core_properties.title = "Engineering Architecture Spec"
    doc.core_properties.author = "System Architect"

    doc.add_heading("Architecture Overview", level=1)
    doc.add_paragraph("This document outlines the distributed ingestion framework.")

    doc.add_heading("Component Specifications", level=2)
    doc.add_paragraph("All workers scale horizontally based on queue depth.")

    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Service"
    hdr_cells[1].text = "SLA"

    row_cells = table.add_row().cells
    row_cells[0].text = "Parser Engine"
    row_cells[1].text = "99.9%"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def sample_pptx_bytes() -> bytes:
    """Generates a valid PPTX presentation with slides and titles."""
    prs = pptx.Presentation()

    # Slide 1: Title
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "AI Roadmap 2026"
    subtitle.text = "Enterprise AI Integration Strategy"

    # Slide 2: Bullets
    bullet_layout = prs.slide_layouts[1]
    slide2 = prs.slides.add_slide(bullet_layout)
    slide2.shapes.title.text = "Core Milestones"
    body = slide2.placeholders[1]
    tf = body.text_frame
    tf.text = "Phase 1: Ingestion Pipeline"
    p = tf.add_paragraph()
    p.text = "Phase 2: Hybrid RAG Search"

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


@pytest.fixture
def sample_csv_bytes() -> bytes:
    """Generates a valid CSV dataset."""
    df = pd.DataFrame({
        "item_id": [101, 102, 103],
        "category": ["Compute", "Storage", "Network"],
        "cost_usd": [450.50, 89.20, 125.00],
        "status": ["Active", "Active", "Pending"],
    })
    return df.to_csv(index=False).encode("utf-8")
