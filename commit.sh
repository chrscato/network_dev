#!/bin/bash

# Commit and push to GitHub
git add .
git commit -m "Update: $(date)"
git push origin master 