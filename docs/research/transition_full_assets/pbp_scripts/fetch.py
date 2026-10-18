import subprocess,json
def get(u):
    for a in range(3):
        r=subprocess.run(['curl','-s','--max-time','40','-A','Mozilla/5.0',u],capture_output=True)
        if r.returncode==0 and r.stdout:
            try: return json.loads(r.stdout)
            except Exception: pass
    return None
