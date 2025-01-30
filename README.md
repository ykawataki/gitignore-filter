# gitignore-filter

A Python library that provides Git-compatible .gitignore pattern filtering with high performance and flexibility. Perfect for building tools that need to process files while respecting Git ignore rules.

## Features

- **Git-Compatible Pattern Matching**: 
  - Full support for all Git pattern syntax
  - Handles multiple .gitignore files with proper precedence
  - Supports negative patterns (`!pattern`)
  - Correctly processes directory-specific patterns
  - Compatible with global gitignore settings

- **High Performance**:
  - Efficient parallel processing for large directories
  - Pattern caching system for faster matching
  - Memory-efficient file system scanning
  - Optimized pattern compilation

- **Robust File Processing**:
  - Proper handling of UTF-8 and other encodings
  - Symlink handling with configurable behavior
  - Handles permission errors gracefully
  - Cross-platform path normalization

- **Flexible Configuration**:
  - Custom pattern support
  - Case sensitivity control
  - Configurable worker count for parallel processing
  - Integration with Git config settings

## Installation

Install from PyPI:
```bash
pip install gitignore-filter
```

Or install from source:
```bash
git clone https://github.com/ykawataki/gitignore-filter.git
cd gitignore-filter
pip install .
```

## Basic Usage

### Python API

```python
from gitignore_filter import git_ignore_filter

# Basic usage
files = git_ignore_filter("./my_project")

# With custom patterns
custom_patterns = [
    "*.log",
    "temp/",
    "!important.log"
]
files = git_ignore_filter("./my_project", custom_patterns=custom_patterns)

# Control case sensitivity
files = git_ignore_filter("./my_project", case_sensitive=True)

# Configure parallel processing
files = git_ignore_filter("./my_project", num_workers=4)
```

## Advanced Features

### Pattern Support

Supports all Git pattern types:
- Basic glob patterns (`*.txt`, `[abc].txt`)
- Character ranges (`[0-9]`, `[a-z]`)
- Single character matching (`?`)
- Directory patterns (`pattern/`)
- Relative paths (`./pattern`, `pattern/subpattern`)
- Recursive matching (`**/pattern`)
- Negative patterns (`!pattern`)
- Pattern escaping (`\#notcomment`)
- Slash patterns (`foo/bar/baz`)
- Root-relative patterns (starting with `/`)
- Brace expansion (`{jpg,jpeg,png}`)
- Negative character classes (`[!abc]`)
- Mid-pattern `**` usage (`foo/**/bar`)
- Directory-only patterns with trailing slash
- Empty pattern handling

### File Processing

- Root .gitignore processing
- Subdirectory .gitignore handling with precedence
- Global gitignore support via core.excludesFile
- Empty line skipping
- Comment handling
- Trailing space removal
- BOM processing
- Absolute path handling
- Path separator normalization
- Empty directory pattern handling
- Symlink handling (configurable)
- Case sensitivity control (core.ignorecase)
- Non-existent directory handling
- UTF-8 conversion for non-UTF-8 .gitignore files
- Windows path separator handling
- Trailing whitespace handling

### Pattern Precedence

The library implements Git's pattern precedence rules:
- Lower-level .gitignore files override higher ones
- Negative patterns override positive ones
- More specific patterns take precedence
- Later patterns in the same file override earlier ones
- Defined precedence between global and local patterns

### Performance Optimization

- Pattern caching mechanism
- Efficient multi-pattern matching
- Fast directory tree traversal
- Parallel processing support

### Special Handling

- Automatic .git directory exclusion
- Relative path return values
- Permission error warnings
- Pathspec-based implementation for simplicity

## Error Handling

The library handles various error conditions gracefully:
- Permission errors
- Missing directories
- Invalid patterns
- Encoding issues
- File system errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

Bug reports and feature requests can be submitted through [GitHub Issues](https://github.com/ykawataki/gitignore-filter/issues).
