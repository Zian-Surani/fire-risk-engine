import urllib.request
import os

urls = {
    "operations_pacman.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzc1OTFmODkzMTgwYTQwMmNiZjUxMjExYmViZmU2ZGJjEgsSBxCqptXF-xUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTI1MjQ4NDk2MzAwNjMwNjIz&filename=&opi=89354086",
    "simulation_pacman.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2Q2OTczNmNhN2Y5NDQ4NjI4ZDNhYjdjOGUzODliYmEwEgsSBxCqptXF-xUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTI1MjQ4NDk2MzAwNjMwNjIz&filename=&opi=89354086",
    "command_center_pacman.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2U1MDVmYThmZTVlYTQ0OTg4YjQ5Yzc1MDM4OGNjN2M3EgsSBxCqptXF-xUYAZIBIwoKcHJvamVjdF9pZBIVQhM0NTI1MjQ4NDk2MzAwNjMwNjIz&filename=&opi=89354086"
}

for filename, url in urls.items():
    print(f"Downloading {filename}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        with open(filename, 'wb') as out_file:
            out_file.write(response.read())
    print(f"Saved {filename}")
