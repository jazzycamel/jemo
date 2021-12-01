# Jemo

## pre-commit
### Setup
```shell
$ poetry run pre-commit install --install-hooks -t pre-commit -t pre-push
```

### Run manually
```shell
# Run the tools that would run before a git push, on only changed files
pre-commit run --hook-stage push

# Run a single tool on all files
pre-commit run --hook-stage manual <tool-id> --all-files

# Run a single tool on specific files
pre-commit run --hook-stage manual <tool-id> --files <files>
```