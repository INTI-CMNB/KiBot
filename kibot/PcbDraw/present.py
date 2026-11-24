# Author: Jan Mrázek
# License: MIT
from pathlib import Path
import sys
import os
import json
import glob
import shutil
import subprocess
import tempfile
import markdown2
from . import pybars
from datetime import datetime

def resolveTemplatePath(path):
    """
    Return a correct template path:
    - if the path matches a directory relative to working directory and the
      directory contains template.json, return that
    - otherwise treat the path as a name into the default template library.
    If none of those are template directories, raise exception.
    """
    if os.path.exists(os.path.join(path, "template.json")):
        return path
    PKG_BASE = os.path.dirname(__file__)
    TEMPLATES = os.path.join(PKG_BASE, "resources/present/templates")
    if os.path.exists(os.path.join(TEMPLATES, path, "template.json")):
        return os.path.join(TEMPLATES, path)
    raise RuntimeError("'{}' is not a name or a path for existing template. Perhaps you miss template.json in the template?".format(path))

def readTemplate(path):
    """
    Resolve template path, read the property file and return a subclass of
    Template which can render the template.
    """
    templateClasses = {
        "HtmlTemplate": HtmlTemplate
    }
    path = resolveTemplatePath(path)
    with open(os.path.join(path, "template.json")) as jsonFile:
        parameters = json.load(jsonFile)
    try:
        tType = parameters["type"]
    except KeyError:
        raise RuntimeError("Invalid template.json - missing 'type'")
    try:
        return templateClasses[tType](path)
    except KeyError:
        raise RuntimeError("Unknown template type '{}'".format(tType))

def copyRelativeTo(sourceTree, sourceFile, outputDir, dry=False):
    sourceTree = os.path.abspath(sourceTree)
    sourceFile = os.path.abspath(sourceFile)
    relPath = os.path.relpath(sourceFile, sourceTree)
    outputDir = os.path.join(outputDir, os.path.dirname(relPath))
    dest = os.path.join(outputDir, os.path.basename(sourceFile))
    if not dry:
        Path(outputDir).mkdir(parents=True, exist_ok=True)
        shutil.copy(sourceFile, outputDir)
    return dest

class Template:
    def __init__(self, directory):
        self.directory = directory
        with open(os.path.join(directory, "template.json")) as jsonFile:
            self.parameters = json.load(jsonFile)
        self.extraResources = []
        self.boards = []
        self.name = None
        self.repository = None

    def _copyResources(self, outputDirectory, dry=False):
        """
        Copy all resource files specified by template.json and further specified
        by addResource to the output directory.
        """
        files = []
        for pattern in self.parameters["resources"]:
            for path in glob.glob(os.path.join(self.directory, pattern), recursive=True):
                files.append(copyRelativeTo(self.directory, path, outputDirectory, dry))
        for pattern in self.extraResources:
            for path in glob.glob(pattern, recursive=True):
                files.append(copyRelativeTo(".", path, outputDirectory, dry))
        return files

    def listResources(self, outputDirectory):
        """
        Returns a list of resources that we will copy.
        """
        return self._copyResources(outputDirectory, dry=True)

    def addResource(self, resource):
        """
        Add a resources. Resource can be specified by a glob pattern. The files
        are treated relative to current working directory.
        """
        self.extraResources.append(resource)

    def addBoard(self, name: str, comment: str, boardfile, front, back, gerbers):
        """
        Add board
        """
        self.boards.append({
            "name": name,
            "comment": comment,
            "source": boardfile,
            "source_front": front,
            "source_back": back,
            "source_gerbers": gerbers
        })

    def _renderBoards(self, outputDirectory):
        """
        Convert all boards to images and gerber exports. Enrich self.boards
        with paths of generated files
        """
        dirPrefix = "boards"
        boardDir = os.path.join(outputDirectory, dirPrefix)
        Path(boardDir).mkdir(parents=True, exist_ok=True)
        for boardDesc in self.boards:
            boardName = os.path.basename(boardDesc["source"]).replace(".kicad_pcb", "")
            boardDesc["front"] = os.path.join(dirPrefix, boardName + "-front"+os.path.splitext(boardDesc["source_front"])[1])
            boardDesc["back"] = os.path.join(dirPrefix, boardName + "-back"+os.path.splitext(boardDesc["source_back"])[1])
            boardDesc["gerbers"] = os.path.join(dirPrefix, boardName + "-gerbers"+os.path.splitext(boardDesc["source_gerbers"])[1])
            boardDesc["file"] = os.path.join(dirPrefix, boardName + ".kicad_pcb")
            shutil.copy(boardDesc["source"], os.path.join(outputDirectory, boardDesc["file"]))
            shutil.copy(boardDesc["source_front"], os.path.join(outputDirectory, boardDesc["front"]))
            shutil.copy(boardDesc["source_back"], os.path.join(outputDirectory, boardDesc["back"]))
            shutil.copy(boardDesc["source_gerbers"], os.path.join(outputDirectory, boardDesc["gerbers"]))

    def render(self, outputDirectory):
        self._copyResources(outputDirectory)
        self._renderBoards(outputDirectory)
        self._renderPage(outputDirectory)

    def gitRevision(self):
        """
        Return a git revision string if in git repo, None otherwise
        """
        if self.git_command is None:
            return None
        proc = subprocess.run([self.git_command, "rev-parse", "HEAD"], capture_output=True)
        if proc.returncode:
            return None
        return proc.stdout.decode("utf-8")

    def currentDateTime(self):
        return datetime.now().strftime("%d. %m. %Y %H:%M")

    def setName(self, name: str):
        self.name = name

    def setRepository(self, rep):
        self.repository = rep


class HtmlTemplate(Template):
    def __init__(self, path):
        super().__init__(path)

    def addDescriptionFile(self, description: str):
        if not description.endswith(".md"):
            raise RuntimeError("Only markdown descriptions are supported for now")
        self.description = markdown2.markdown_path(description, extras=["fenced-code-blocks"])

    def _renderPage(self, outputDirectory):
        with open(os.path.join(self.directory, "index.html")) as templateFile:
            template = pybars.Compiler().compile(templateFile.read())
        gitRev = self.gitRevision()
        content = template({
            "repo": self.repository,
            "gitRev": gitRev,
            "gitRevShort": gitRev[:7] if gitRev else None,
            "datetime": self.currentDateTime(),
            "name": self.name,
            "boards": self.boards,
            "description": self.description
        })
        with open(os.path.join(outputDirectory, "index.html"),"w") as outFile:
            outFile.write(content)

def boardpage(outdir, description: str, board, resource, template, repository, name: str, git_command):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    template = readTemplate(template)
    template.git_command = git_command
    template.addDescriptionFile(description)
    template.setRepository(repository)
    template.setName(name)
    for r in resource:
        template.addResource(r)
    for name, comment, file, front, back, gerbers in board:
        template.addBoard(name, comment, file, front, back, gerbers)
    template.render(outdir)
