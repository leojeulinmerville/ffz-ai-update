import os

env_path = ".env"
new_url = "DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ffz_db"

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("DATABASE_URL="):
            new_lines.append(new_url + "\n")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append("\n" + new_url + "\n")
        
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    print("Updated .env")
else:
    with open(env_path, "w") as f:
        f.write(new_url + "\n")
    print("Created .env")
