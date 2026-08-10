# Synthetic outputs

Run the following from the public-template root to refresh this directory:

```bash
python -m elitecv build --root examples/synthetic-profile --target robotics-software --output-dir examples/synthetic-profile/outputs
python -m elitecv build --root examples/synthetic-profile --target ai-internship --output-dir examples/synthetic-profile/outputs
```

Generated target directories are intentionally separate from the private
`dist/` default. They contain only fictional sample data.
