"""Text reader tool unit tests."""

from pathlib import Path

from app.tools.text_tool import TextReaderTool, read_text_file


def test_read_text_file(tmp_path: Path) -> None:
    """Plain text files are read correctly."""
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Hello OmniAgent", encoding="utf-8")

    content = read_text_file(str(file_path))
    assert content == "Hello OmniAgent"


def test_text_reader_tool(tmp_path: Path) -> None:
    """TextReaderTool returns ToolResult on success."""
    file_path = tmp_path / "data.txt"
    file_path.write_text("sample content", encoding="utf-8")

    tool = TextReaderTool()
    result = tool.run(file_path=str(file_path))

    assert result.success is True
    assert result.output_text == "sample content"
