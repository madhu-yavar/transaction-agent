from cloud.drive_auth import authenticate_drive, list_drive_files, download_drive_file

service = authenticate_drive()
files = list_drive_files(service)

print(\"Available Files:\")
for i, f in enumerate(files):
    print(f\"{i+1}. {f['name']} ({f['mimeType']})\")

choice = int(input(\"Enter file number to download: \")) - 1
file_path = download_drive_file(service, files[choice]['id'], files[choice]['name'])

print(f\"✅ File downloaded to: {file_path}\")
