#!/bin/bash
# Test LaTeX installation in Docker container

echo "=== Testing LaTeX/Pandoc Installation ==="
echo ""

echo "1. Checking if Pandoc is installed..."
if command -v pandoc &> /dev/null; then
    echo "✓ Pandoc found:"
    pandoc --version | head -1
else
    echo "✗ Pandoc NOT found"
    exit 1
fi
echo ""

echo "2. Checking if XeLaTeX is installed..."
if command -v xelatex &> /dev/null; then
    echo "✓ XeLaTeX found:"
    xelatex --version | head -1
else
    echo "✗ XeLaTeX NOT found"
    exit 1
fi
echo ""

echo "3. Testing PDF generation with simple markdown..."
cat > /tmp/test.md <<'EOF'
# Test Document

This is a **test** document to verify PDF generation.

## Section 1

Some content here.
EOF

echo "Markdown content:"
cat /tmp/test.md
echo ""

echo "4. Attempting PDF generation with XeLaTeX..."
pandoc /tmp/test.md -o /tmp/test.pdf --pdf-engine=xelatex -V geometry:margin=1in 2>&1

if [ -f /tmp/test.pdf ]; then
    echo "✓ PDF generated successfully!"
    echo "PDF size: $(ls -lh /tmp/test.pdf | awk '{print $5}')"
    echo "PDF location: /tmp/test.pdf"
else
    echo "✗ PDF generation FAILED"
    echo "Error output above shows the issue"
    exit 1
fi
echo ""

echo "5. Checking installed TeX packages..."
echo "Checking for critical packages..."
for pkg in geometry hyperref booktabs fontspec unicode-math; do
    if kpsewhich ${pkg}.sty &> /dev/null; then
        echo "  ✓ ${pkg}.sty found"
    else
        echo "  ✗ ${pkg}.sty NOT found"
    fi
done
echo ""

echo "=== All tests passed! LaTeX is working correctly. ==="
