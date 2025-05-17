#!/bin/bash

# Deploy Terraform infrastructure
cd backend/terraform
terraform init
terraform apply -auto-approve

# Package and deploy Lambda functions
cd ../lambda_functions
for dir in */ ; do
    cd "$dir"
    pip install -r requirements.txt -t .
    zip -r ../${dir%/}.zip .
    aws lambda update-function-code --function-name ${dir%/} --zip-file fileb://../${dir%/}.zip
    cd ..
done

# Deploy frontend
cd ../../frontend
pip install -r requirements.txt
gunicorn app:app -b 0.0.0.0:8000