import streamlit as st
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import os
import io
import uuid
import tempfile
import base64

# Configuration
DPI = 300  # high quality

# Initialize session state
if 'preview_image' not in st.session_state:
    st.session_state.preview_image = None
if 'output_pdf_bytes' not in st.session_state:
    st.session_state.output_pdf_bytes = None

# Utility functions
def mm_to_px(mm, dpi=DPI):
    inches = mm / 25.4
    return int(round(inches * dpi))

# Build A4 template (300 DPI) with 4 slots of 100x150 mm each
def build_template_image(bg_color=(255, 255, 255)):
    # A4 size in mm
    a4_w_mm, a4_h_mm = 210, 297
    # label size
    label_w_mm, label_h_mm = 100, 150
    # margins and gaps (mm)
    margin_x_mm = 5
    margin_y_mm = 5
    gap_x_mm = 5
    gap_y_mm = 5

    # convert to pixels
    a4_w = mm_to_px(a4_w_mm)
    a4_h = mm_to_px(a4_h_mm)
    label_w = mm_to_px(label_w_mm)
    label_h = mm_to_px(label_h_mm)
    margin_x = mm_to_px(margin_x_mm)
    margin_y = mm_to_px(margin_y_mm)
    gap_x = mm_to_px(gap_x_mm)
    gap_y = mm_to_px(gap_y_mm)

    im = Image.new('RGB', (a4_w, a4_h), color=bg_color)

    # compute positions for 2x2 grid (col 0..1, row 0..1)
    positions = []
    for row in range(2):
        for col in range(2):
            x = margin_x + col * (label_w + gap_x)
            # y origin is top: PIL uses (0,0) top-left
            y = margin_y + row * (label_h + gap_y)
            positions.append((x, y))
    return im, positions, (label_w, label_h)

# Convert uploaded PDF to image (first page)
def pdf_to_image(pdf_bytes, dpi=DPI):
    # Create a temporary file to save PDF bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_file_path = tmp_file.name
    
    try:
        images = convert_from_path(tmp_file_path, dpi=dpi, first_page=1, last_page=1)
        if not images:
            raise RuntimeError('Failed to convert PDF to image')
        return images[0]
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

# Paste label image into a chosen slot (1..4)
def paste_label_onto_template(label_img, slot_number):
    template, positions, label_size = build_template_image()
    label_w, label_h = label_size

    # Resize label_img to fit into label_size while preserving aspect ratio
    label_img = ImageOps.exif_transpose(label_img)
    label_img.thumbnail((label_w, label_h), Image.LANCZOS)

    # center the label within the slot
    x, y = positions[slot_number - 1]
    paste_x = x + (label_w - label_img.width) // 2
    paste_y = y + (label_h - label_img.height) // 2

    template.paste(label_img, (paste_x, paste_y))
    return template

def paste_labels_onto_template(label_imgs, slot_numbers):
    template, positions, label_size = build_template_image()
    label_w, label_h = label_size
    for label_img, slot_number in zip(label_imgs, slot_numbers):
        label_img = ImageOps.exif_transpose(label_img)
        label_img.thumbnail((label_w, label_h), Image.LANCZOS)
        x, y = positions[slot_number - 1]
        paste_x = x + (label_w - label_img.width) // 2
        paste_y = y + (label_h - label_img.height) // 2
        template.paste(label_img, (paste_x, paste_y))
    return template

def image_to_pdf_bytes(image):
    """Convert PIL Image to PDF bytes"""
    pdf_bytes = io.BytesIO()
    img_rgb = image.convert('RGB')
    img_rgb.save(pdf_bytes, format='PDF', resolution=DPI)
    pdf_bytes.seek(0)
    return pdf_bytes.getvalue()

def get_download_link(pdf_bytes, filename):
    """Generate a download link for PDF bytes"""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Download PDF</a>'

# Streamlit App
def main():
    st.set_page_config(
        page_title="Meesho 4-Slot Label Composer", 
        page_icon="📄", 
        layout="wide"
    )
    
    st.title("📄 Meesho 4-Slot Label Composer")
    st.markdown("Upload up to 4 single-page PDF labels and position them on an A4 template with 4 slots")
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload & Configure")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose up to 4 PDF files", 
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload up to 4 single-page PDF labels"
        )
        
        slot_numbers = []
        if uploaded_files:
            for i, file in enumerate(uploaded_files):
                slot = st.selectbox(
                    f"Select slot for PDF {i+1}",
                    options=[1, 2, 3, 4],
                    index=i if i < 4 else 0,
                    key=f"slot_select_{i}",
                    help="Choose which slot to place your label in: 1: Top-left, 2: Top-right, 3: Bottom-left, 4: Bottom-right"
                )
                slot_numbers.append(slot)
        
        # Visual slot layout guide
        st.markdown("**Slot Layout:**")
        slot_layout = """
        ```
        A4 Template Layout
        ┌─────────────────┐
        │  [1]    [2]    │
        │                │
        │  [3]    [4]    │
        └─────────────────┘
        ```
        """
        st.markdown(slot_layout)
        
        # Process button
        if st.button("🔄 Generate Preview", type="primary"):
            if uploaded_files and slot_numbers:
                try:
                    # Show progress
                    with st.spinner("Processing PDFs and generating preview..."):
                        label_imgs = []
                        for file in uploaded_files:
                            pdf_bytes = file.read()
                            label_img = pdf_to_image(pdf_bytes)
                            label_imgs.append(label_img)
                        output_image = paste_labels_onto_template(label_imgs, slot_numbers)
                        
                        # Store in session state
                        st.session_state.preview_image = output_image
                        st.session_state.output_pdf_bytes = image_to_pdf_bytes(output_image)
                        
                    st.success("✅ Preview generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error processing PDFs: {str(e)}")
            else:
                st.warning("⚠️ Please upload PDF files and select slots")
    
    with col2:
        st.header("👁️ Preview & Download")
        
        if st.session_state.preview_image is not None:
            # Display preview
            st.image(
                st.session_state.preview_image, 
                caption="A4 Template Preview",
                use_container_width=True
            )
            
            # Download section
            if st.session_state.output_pdf_bytes is not None:
                st.markdown("### 📥 Download")
                
                # Create download button
                st.download_button(
                    label="📄 Download as PDF",
                    data=st.session_state.output_pdf_bytes,
                    file_name="meesho_label_template.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
                
                # Show file info
                pdf_size_kb = len(st.session_state.output_pdf_bytes) / 1024
                st.info(f"📊 PDF Size: {pdf_size_kb:.1f} KB | Resolution: {DPI} DPI")
        else:
            # Placeholder when no preview
            st.markdown("### 🎯 Preview will appear here")
            st.info("Upload PDFs and click 'Generate Preview' to see your labels positioned on the A4 template")
            
            # Show empty template as reference
            empty_template, _, _ = build_template_image()
            st.image(
                empty_template, 
                caption="Empty A4 Template (Reference)",
                use_container_width=True
            )
    
    # Additional information
    st.markdown("---")
    st.markdown("### ℹ️ Information")
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.metric("📄 Template Size", "A4 (210×297 mm)")
    
    with col_info2:
        st.metric("🏷️ Label Size", "100×150 mm")
    
    with col_info3:
        st.metric("🔍 Resolution", f"{DPI} DPI")
    
    # Technical details
    with st.expander("🔧 Technical Details"):
        st.markdown("""
        - **Template**: A4 size with 4 equal slots arranged in 2×2 grid
        - **Label dimensions**: 100mm × 150mm each
        - **Margins**: 5mm from edges
        - **Gap between labels**: 5mm horizontal and vertical
        - **Output format**: High-quality PDF at 300 DPI
        - **Supported input**: Up to 4 single-page PDF files only
        """)

if __name__ == "__main__":
    main()