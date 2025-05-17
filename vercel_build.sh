#!/bin/bash
# Instalar dependências do sistema
apt-get update -y
apt-get install -y poppler-utils

# Instalar dependências Python
pip install -r requirements.txt