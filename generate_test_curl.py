import base64

file_path = 'textextract-bad1.pdf'
with open(file_path, 'rb') as file:
    encoded_file = base64.b64encode(file.read()).decode('utf-8')

curl_command = f'curl -X POST "https://owu9p0i146.execute-api.us-east-1.amazonaws.com/dev/files" \
    -H "Content-Type: application/json" \
    -d \'{{"file": "{encoded_file}"}}\''

print(curl_command)
