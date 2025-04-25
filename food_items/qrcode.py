import qrcode
from io import BytesIO

# Generate QR codes for table numbers 1 to 10 and save them as PNG images
qr_images = {}
for table_number in range(1, 11):
    login_url = f"http://192.168.0.109:8000/login/{table_number}/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(login_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image to a BytesIO buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    qr_images[f"table_{table_number}_qr.png"] = buffer

# Save one sample QR code (e.g., table_1_qr.png) to show here
sample_qr_path = "/mnt/data/table_1_qr.png"
with open(sample_qr_path, 'wb') as f:
    f.write(qr_images['table_1_qr.png'].getvalue())

sample_qr_path
