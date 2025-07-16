import os
import tempfile
import yaml
import pytest
from datetime import datetime, timedelta
from collections import namedtuple

# Dummy message and author for testing purpose
DummyAuthor = namedtuple("DummyAuthor", ["id", "name"])
DummyAttachment = namedtuple("DummyAttachment", ["filename"])

class DummyMessage:
    def __init__(self, content, author, attachments=None, mentions=None):
        self.content = content
        self.author = author
        self.attachments = attachments or []
        self.mentions = mentions or []
        
# Import our Automoderator from the source directory
from src.automoderation.automod import Automoderator

@pytest.fixture
def config_file():
    # Create a temporary YAML config file
    config_data = {
        "badword_rule": {"bad_words": ["badword1", "badword2"]},
        "link_blocking_rule": {"blocked_links": ["discord.gg", "bit.ly"]},
        "mass_mention_rule": {"max_mentions": 2},
        "caps_rule": {"max_caps_ratio": 0.7, "min_length": 5},
        "attachment_rule": {"blocked_filetypes": [".exe"]},
        "spam_rule": {"spam_interval": 2, "spam_threshold": 3}
    }
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w")
    yaml.dump(config_data, temp)
    temp.close()
    yield temp.name
    os.remove(temp.name)

def test_badword_rule(config_file):
    automod = Automoderator(config_file)
    author = DummyAuthor(id=1, name="TestUser")
    # Test triggering bad word
    message = DummyMessage("This contains badword1", author)
    # We expect handle_warning to be called (here print to console)—for tests, you could mock handle_warning.
    automod.check_message(message)
    
def test_link_rule(config_file):
    automod = Automoderator(config_file)
    author = DummyAuthor(id=2, name="TestUser2")
    message = DummyMessage("Join discord.gg/someinvite", author)
    automod.check_message(message)

def test_mass_mention_rule(config_file):
    automod = Automoderator(config_file)
    author = DummyAuthor(id=3, name="TestUser3")
    # Create dummy mentions that exceed allowed number.
    mentions = [DummyAuthor(id=i, name=f"User{i}") for i in range(3)]
    message = DummyMessage("Hello", author, mentions=mentions)
    automod.check_message(message)

def test_caps_rule(config_file):
    automod = Automoderator(config_file)
    author = DummyAuthor(id=4, name="TestUser4")
    # Create message with too many uppercase letters
    message = DummyMessage("THIS IS WAY TOO LOUD", author)
    automod.check_message(message)

def test_attachment_rule(config_file):
    automod = Automoderator(config_file)
    author = DummyAuthor(id=5, name="TestUser5")
    # Create a dummy attachment with a blocked file type
    attachment = DummyAttachment(filename="test.exe")
    message = DummyMessage("File attached", author, attachments=[attachment])
    automod.check_message(message)

def test_spam_rule(config_file):
    automod = Automoderator(config_file)
    author = DummyAuthor(id=6, name="TestUser6")
    message = DummyMessage("Spam message", author)

    # Call check_message multiple times to simulate spam—use a short delay if needed.
    for _ in range(4):
        automod.check_message(message)