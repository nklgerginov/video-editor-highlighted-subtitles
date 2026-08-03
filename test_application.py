#!/usr/bin/env python3
"""
Test script to verify the application works correctly.
"""
import os
import sys
import tempfile
from pathlib import Path

# Set offscreen platform for Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add the project directory to the path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from models import VideoProject, Word, SubtitleLine, SubtitleStyle, SubtitlePosition
        print("  ✓ models.py")
        from processing import SubtitleGenerator
        print("  ✓ processing.py")
        from export import VideoExporter
        print("  ✓ export.py")
        from ui.main_window import MainWindow
        print("  ✓ ui/main_window.py")
        from ui.preview import VideoPreviewWidget, VideoPreviewScene, SubtitleBox
        print("  ✓ ui/preview.py")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_models():
    """Test the data models."""
    print("\nTesting models...")
    try:
        from models import Word, SubtitleLine, VideoProject, SubtitleStyle, SubtitlePosition
        
        # Test Word
        word = Word(text="hello", start_time=0.0, end_time=0.5)
        assert word.text == "hello"
        assert word.start_time == 0.0
        assert word.end_time == 0.5
        print("  ✓ Word model")
        
        # Test SubtitleLine
        line = SubtitleLine()
        line.add_word(Word(text="hello", start_time=0.0, end_time=0.5))
        line.add_word(Word(text="world", start_time=0.5, end_time=1.0))
        assert len(line.words) == 2
        assert line.text == "hello world"
        print("  ✓ SubtitleLine model")
        
        # Test VideoProject
        project = VideoProject(
            video_path="/fake/video.mp4",
            vosk_model_path="/fake/model"
        )
        project.subtitles.append(line)
        assert len(project.get_all_words()) == 2
        active = project.get_active_word_at_time(0.25)
        assert active is not None
        assert active.text == "hello"
        print("  ✓ VideoProject model")
        
        return True
    except Exception as e:
        print(f"  ✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processing():
    """Test the processing module."""
    print("\nTesting processing...")
    try:
        from processing import SubtitleGenerator
        import tempfile
        
        # Create a fake vosk model directory
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "fake-model")
            os.makedirs(model_path, exist_ok=True)
            with open(os.path.join(model_path, "model.conf"), "w") as f:
                f.write("fake model config")
            
            # Test model validation
            gen = SubtitleGenerator(model_path)
            assert gen.vosk_model_path == model_path
            print("  ✓ SubtitleGenerator initialization")
            
            # Test invalid model path
            try:
                SubtitleGenerator("/nonexistent/path")
                print("  ✗ Should have raised FileNotFoundError")
                return False
            except FileNotFoundError:
                print("  ✓ FileNotFoundError for invalid model path")
        
        return True
    except Exception as e:
        print(f"  ✗ Processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_export():
    """Test the export module."""
    print("\nTesting export...")
    try:
        from export import VideoExporter
        from models import VideoProject, Word, SubtitleLine, SubtitleStyle, SubtitlePosition
        
        # Create a test project
        project = VideoProject(
            video_path="/fake/video.mp4",
            vosk_model_path="/fake/model"
        )
        
        # Add some subtitles
        line = SubtitleLine()
        line.add_word(Word(text="hello", start_time=0.0, end_time=0.5))
        line.add_word(Word(text="world", start_time=0.5, end_time=1.0))
        project.subtitles.append(line)
        
        # Test VideoExporter initialization
        exporter = VideoExporter(project)
        assert exporter.project == project
        print("  ✓ VideoExporter initialization")
        
        # Test _get_font_path
        font_path = exporter._get_font_path("Arial")
        print(f"  ✓ Font path lookup (found: {font_path is not None})")
        
        return True
    except Exception as e:
        print(f"  ✗ Export test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui():
    """Test the UI components."""
    print("\nTesting UI...")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        from ui.preview import VideoPreviewWidget, VideoPreviewScene, SubtitleBox
        
        # Create QApplication
        app = QApplication.instance() or QApplication([])
        
        # Test MainWindow creation
        window = MainWindow()
        assert window is not None
        print("  ✓ MainWindow creation")
        
        # Test VideoPreviewWidget
        preview = VideoPreviewWidget()
        assert preview is not None
        print("  ✓ VideoPreviewWidget creation")
        
        # Test SubtitleBox
        box = SubtitleBox(50, 50, 800, 200)
        assert box is not None
        print("  ✓ SubtitleBox creation")
        
        return True
    except Exception as e:
        print(f"  ✗ UI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Video Editor - Highlighted Subtitles Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Models", test_models()))
    results.append(("Processing", test_processing()))
    results.append(("Export", test_export()))
    results.append(("UI", test_ui()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
