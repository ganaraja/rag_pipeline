import os
import tempfile
import atexit
import shutil

# Create a temporary directory for Qdrant during tests
temp_qdrant_dir = tempfile.mkdtemp()
os.environ["QDRANT_PATH"] = temp_qdrant_dir

def cleanup():
    shutil.rmtree(temp_qdrant_dir, ignore_errors=True)

atexit.register(cleanup)

# Avoid torch.load security vulnerability ValueError in sentence-transformers
os.environ["TORCH_LOAD_WEIGHTS_ONLY"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Set testing flag to mock out Heavy initializations if main.py handles it
os.environ["TESTING"] = "1"
