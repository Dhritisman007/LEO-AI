"""
Language-specific code quality rules injected per-task based on detected language.
"""

STYLE_GUIDES = {
    "python": """
PYTHON QUALITY CHECKLIST — verify before finalizing:
□ All functions have type hints: def process(data: list[str]) -> dict:
□ All functions have docstrings with Args/Returns/Raises sections
□ Used dataclasses or pydantic for data structures, not plain dicts
□ Used pathlib.Path not os.path for file operations
□ Used f-strings not .format() or % formatting
□ Named constants defined at module level (MAX_SIZE = 100)
□ Edge cases handled: empty list, None input, zero division
□ Specific exceptions raised: ValueError not Exception
□ Context managers used for file/resource handling
□ __all__ defined if this is a module meant for import
□ if __name__ == '__main__': guard for executable scripts

EXAMPLE of production-quality Python function:
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

MAX_ITEMS = 1000

@dataclass
class ProcessResult:
    total: int
    processed: int
    errors: list[str]

def process_items(
    items: list[str],
    output_path: Optional[Path] = None
) -> ProcessResult:
    \"\"\"
    Process a list of items and optionally save results.
    
    Args:
        items: List of strings to process. Must not be empty.
        output_path: Optional path to save results. Creates dirs if needed.
    
    Returns:
        ProcessResult with counts and any errors encountered.
    
    Raises:
        ValueError: If items is empty or exceeds MAX_ITEMS.
        IOError: If output_path cannot be written.
    
    Example:
        >>> result = process_items(['a', 'b', 'c'])
        >>> print(result.processed)
        3
    \"\"\"
    if not items:
        raise ValueError("items cannot be empty")
    if len(items) > MAX_ITEMS:
        raise ValueError(f"items length {len(items)} exceeds MAX_ITEMS {MAX_ITEMS}")
    
    errors = []
    processed = 0
    
    for item in items:
        try:
            # Process logic here
            processed += 1
        except Exception as e:
            errors.append(f"Failed to process '{item}': {e}")
    
    result = ProcessResult(total=len(items), processed=processed, errors=errors)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(result))
    
    return result
```
""",

    "javascript": """
JAVASCRIPT/TYPESCRIPT QUALITY CHECKLIST:
□ TypeScript types on all function params and return values
□ const for everything, let only when reassignment needed, never var
□ async/await not .then() chains
□ Optional chaining: user?.profile?.name
□ Nullish coalescing: value ?? defaultValue
□ Destructuring in function params
□ Early returns to reduce nesting
□ Error handling with try/catch on all async operations
□ JSDoc comments on all exported functions
□ Input validation at function entry points

EXAMPLE of production-quality TypeScript:
```typescript
interface ProcessResult {
  total: number;
  processed: number;
  errors: string[];
}

/**
 * Process a list of items asynchronously.
 * @param items - Array of strings to process
 * @param options - Optional configuration
 * @returns Promise resolving to ProcessResult
 * @throws {Error} If items array is empty
 */
async function processItems(
  items: string[],
  options: { maxConcurrent?: number } = {}
): Promise<ProcessResult> {
  if (!items.length) {
    throw new Error('items array cannot be empty');
  }

  const { maxConcurrent = 5 } = options;
  const errors: string[] = [];
  let processed = 0;

  for (const item of items) {
    try {
      await processItem(item);
      processed++;
    } catch (error) {
      errors.push(`Failed: ${item}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  return { total: items.length, processed, errors };
}
```
""",

    "java": """
JAVA QUALITY CHECKLIST:
□ Follow Oracle naming: PascalCase classes, camelCase methods/vars, UPPER_SNAKE constants
□ Every class has a Javadoc comment
□ Every public method has a Javadoc with @param @return @throws
□ Use Optional<T> instead of returning null
□ Use try-with-resources for all closeable resources
□ Use Stream API for collection operations
□ Use final for variables that won't be reassigned
□ Interfaces over concrete types in method signatures
□ Validate constructor params, throw IllegalArgumentException for invalid input
□ Override equals() and hashCode() for value objects

EXAMPLE of production-quality Java:
```java
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Processes a list of items and returns results.
 */
public class ItemProcessor {
    
    private static final int MAX_ITEMS = 1000;
    
    /**
     * Processes items and returns successful results.
     *
     * @param items the list of items to process, must not be null or empty
     * @return list of processed results
     * @throws IllegalArgumentException if items is null, empty, or exceeds MAX_ITEMS
     */
    public List<String> processItems(final List<String> items) {
        if (items == null || items.isEmpty()) {
            throw new IllegalArgumentException("items must not be null or empty");
        }
        if (items.size() > MAX_ITEMS) {
            throw new IllegalArgumentException(
                String.format("items size %d exceeds maximum %d", items.size(), MAX_ITEMS)
            );
        }
        
        return items.stream()
            .filter(item -> item != null && !item.isBlank())
            .map(this::processItem)
            .flatMap(Optional::stream)
            .collect(Collectors.toList());
    }
    
    private Optional<String> processItem(final String item) {
        try {
            return Optional.of(item.trim().toUpperCase());
        } catch (Exception e) {
            System.err.println("Failed to process item: " + item + " — " + e.getMessage());
            return Optional.empty();
        }
    }
}
```
""",

    "cpp": """
C++ QUALITY CHECKLIST:
□ RAII for all resource management
□ Smart pointers: unique_ptr, shared_ptr — never raw new/delete
□ const correctness: const on methods that don't modify state
□ std::string not char*, std::vector not C arrays
□ nullptr not NULL or 0
□ Range-based for loops
□ Override and final keywords on virtual methods
□ Explicit constructors to prevent implicit conversion
□ Rule of zero/three/five followed

EXAMPLE of production-quality C++:
```cpp
#include <string>
#include <vector>
#include <stdexcept>
#include <memory>

class ItemProcessor {
public:
    static constexpr size_t MAX_ITEMS = 1000;
    
    explicit ItemProcessor(size_t maxConcurrent = 5)
        : maxConcurrent_(maxConcurrent) {}
    
    // Prevent copying — use move semantics instead
    ItemProcessor(const ItemProcessor&) = delete;
    ItemProcessor& operator=(const ItemProcessor&) = delete;
    ItemProcessor(ItemProcessor&&) = default;
    
    /**
     * Process a list of items.
     * @throws std::invalid_argument if items is empty or exceeds MAX_ITEMS
     */
    std::vector<std::string> processItems(
        const std::vector<std::string>& items) const {
        
        if (items.empty()) {
            throw std::invalid_argument("items cannot be empty");
        }
        if (items.size() > MAX_ITEMS) {
            throw std::invalid_argument("items exceeds maximum size");
        }
        
        std::vector<std::string> results;
        results.reserve(items.size());
        
        for (const auto& item : items) {
            if (!item.empty()) {
                results.push_back(processItem(item));
            }
        }
        return results;
    }

private:
    size_t maxConcurrent_;
    
    std::string processItem(const std::string& item) const {
        return item; // implement processing logic here
    }
};
```
""",

    "go": """
GO QUALITY CHECKLIST:
□ Errors returned as values, always checked
□ Error messages lowercase, no punctuation
□ Short variable names ok in short scopes, descriptive in long ones
□ defer for cleanup operations
□ Interfaces defined where they're used, not where implemented
□ Table-driven tests
□ Context propagation for cancellation
□ Exported names have godoc comments
□ No naked returns
□ Group imports: stdlib, external, internal

EXAMPLE of production-quality Go:
```go
package processor

import (
    "errors"
    "fmt"
)

const maxItems = 1000

// ProcessResult holds the outcome of a processing operation.
type ProcessResult struct {
    Total     int
    Processed int
    Errors    []string
}

// ProcessItems processes a slice of items and returns results.
// Returns an error if items is empty or exceeds the maximum size.
func ProcessItems(items []string) (ProcessResult, error) {
    if len(items) == 0 {
        return ProcessResult{}, errors.New("items cannot be empty")
    }
    if len(items) > maxItems {
        return ProcessResult{}, fmt.Errorf("items length %d exceeds maximum %d", len(items), maxItems)
    }
    
    result := ProcessResult{Total: len(items)}
    
    for _, item := range items {
        if err := processItem(item); err != nil {
            result.Errors = append(result.Errors, fmt.Sprintf("failed %q: %v", item, err))
            continue
        }
        result.Processed++
    }
    
    return result, nil
}

func processItem(item string) error {
    if item == "" {
        return errors.New("item cannot be empty")
    }
    // processing logic here
    return nil
}
```
""",

    "rust": """
RUST QUALITY CHECKLIST:
□ Result<T, E> for all fallible operations — no unwrap() in non-test code
□ Custom error types implementing std::error::Error
□ Ownership semantics respected — minimize cloning
□ Derive common traits: Debug, Clone, PartialEq where appropriate
□ Use ? operator for error propagation
□ Doc comments with examples that run as doctests
□ No unsafe unless absolutely necessary with safety comment explaining why
□ Use iterators and functional style over manual loops

EXAMPLE of production-quality Rust:
```rust
use std::fmt;

const MAX_ITEMS: usize = 1000;

#[derive(Debug)]
pub enum ProcessError {
    EmptyInput,
    TooManyItems { count: usize, max: usize },
    ItemFailed { item: String, reason: String },
}

impl fmt::Display for ProcessError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyInput => write!(f, "input cannot be empty"),
            Self::TooManyItems { count, max } => {
                write!(f, "item count {count} exceeds maximum {max}")
            }
            Self::ItemFailed { item, reason } => {
                write!(f, "failed to process '{item}': {reason}")
            }
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct ProcessResult {
    pub total: usize,
    pub processed: usize,
    pub errors: Vec<String>,
}

/// Processes a slice of items.
///
/// # Errors
/// Returns `ProcessError::EmptyInput` if items is empty.
/// Returns `ProcessError::TooManyItems` if items exceeds MAX_ITEMS.
///
/// # Example
/// ```
/// let result = process_items(&["hello", "world"]).unwrap();
/// assert_eq!(result.processed, 2);
/// ```
pub fn process_items(items: &[&str]) -> Result<ProcessResult, ProcessError> {
    if items.is_empty() {
        return Err(ProcessError::EmptyInput);
    }
    if items.len() > MAX_ITEMS {
        return Err(ProcessError::TooManyItems {
            count: items.len(),
            max: MAX_ITEMS,
        });
    }

    let mut errors = Vec::new();
    let processed = items
        .iter()
        .filter(|&&item| {
            if item.is_empty() {
                errors.push(format!("skipped empty item"));
                false
            } else {
                true
            }
        })
        .count();

    Ok(ProcessResult {
        total: items.len(),
        processed,
        errors,
    })
}
```
""",
}


def get_style_guide(language: str) -> str:
    """Return the style guide for a given language."""
    normalized = language.lower().strip()
    aliases = {
        "js": "javascript",
        "ts": "typescript",
        "typescript": "javascript",
        "c++": "cpp",
        "cc": "cpp",
        "golang": "go",
        "rs": "rust",
    }
    normalized = aliases.get(normalized, normalized)
    return STYLE_GUIDES.get(normalized, "")


def detect_language_from_task(task: str) -> str | None:
    """Detect which language a task is asking for."""
    task_lower = task.lower()
    signals = {
        "python": ["python", ".py", "django", "flask", "fastapi", "pandas", "numpy"],
        "javascript": ["javascript", "js", "node", "react", "vue", "typescript", "ts"],
        "java": ["java", ".java", "spring", "maven", "gradle"],
        "cpp": ["c++", "cpp", ".cpp", "cmake"],
        "c": [" in c ", "in c,", ".c file", "c program"],
        "go": ["golang", " in go", "go program", ".go"],
        "rust": ["rust", ".rs", "cargo"],
    }
    for lang, keywords in signals.items():
        if any(kw in task_lower for kw in keywords):
            return lang
    return None
