FROM kluisz/kluisz-ai-canvas:1.0-alpha

CMD ["python", "-m", "kluisz", "run", "--host", "0.0.0.0", "--port", "7860"]
