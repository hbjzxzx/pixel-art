# Dev run:
export PYTHONPATH=`pwd`
python api/app.py

# Prod run: onlu in docker
docker run -d -p 8501:8501 290007431/pixel-art:0.0.2