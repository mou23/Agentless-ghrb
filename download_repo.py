import os
import sys
import subprocess

def repo_name_from_url(url: str) -> str:
    name = url.rstrip('/').split('/')[-1]
    # Remove the exact ".git" suffix if present
    if name.endswith(".git"):
        name = name[:-4]
    # Special case rename
    if name == "incubator-seata":
        name = "seata"
    return name

# List of Git repository URLs
repos = [
    "https://github.com/iBotPeaches/Apktool.git",
    "https://github.com/assertj/assertj.git",
    "https://github.com/checkstyle/checkstyle.git",
    "https://github.com/apache/dubbo.git",
    "https://github.com/alibaba/fastjson.git",
    "https://github.com/FasterXML/jackson-core.git",
    "https://github.com/FasterXML/jackson-dataformat-xml.git",
    "https://github.com/FasterXML/jackson-databind.git",
    "https://github.com/jhy/jsoup.git",
    "https://github.com/alibaba/nacos.git",
    "https://github.com/google/gson.git",
    "https://github.com/OpenAPITools/openapi-generator.git",
    "https://github.com/square/retrofit.git",
    "https://github.com/apache/incubator-seata.git",
    "https://github.com/apache/rocketmq.git",
    "https://github.com/Hakky54/sslcontext-kickstart.git"
]

target_dir = sys.argv[1] if len(sys.argv) > 1 else "projects"
os.makedirs(target_dir, exist_ok=True)

for url in repos:
    repo_name = repo_name_from_url(url)
    
    dest = os.path.join(target_dir, repo_name)
    
    if not os.path.exists(dest):
        print(f"Cloning {repo_name}...")
        result = subprocess.run(["git", "clone", url, dest])
        if result.returncode != 0:
            print(f"[ERROR] Failed to clone {repo_name}")
            continue
