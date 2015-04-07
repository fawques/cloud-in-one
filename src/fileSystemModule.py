import os.path
import os
import hashlib
from functools import partial
from log import Logger


class FileSystemModule():
    """docstring for FileSystemModule"""
    def __init__(self, path):
        self.logger = Logger(__name__)
        self.logger.info("Creating FileSystemModule")

        self.logger.debug("path = <" + path + ">")
        self.main_path = os.path.normpath(os.path.expanduser(path))
        self.logger.debug("self.main_path = <" + self.main_path + ">")

        try:
            if not os.path.isdir(self.main_path):
                os.makedirs(self.main_path, exist_ok=True)
        except:
            self.logger.debug("error when trying to create folder " + self.main_path + "trying with homeDir")
            self.main_path = self.getFullPath(self.getHomeDir(), self.main_path.split("/")[-1])

    def createDirectory(self, dir_path):
        fullpath = self.getFullPath(self.main_path, dir_path)
        self.logger.debug("Creating directory <" + fullpath + ">")
        os.makedirs(fullpath, exist_ok=True)
        return fullpath

    def createFile(self, file_path, stream):
        self.logger.debug("Creating file <" + file_path + ">")
        fullpath = self.getFullPath(self.main_path, file_path)
        self.logger.debug("File fullpath <" + fullpath + ">")
        if "/" in file_path:
            self.createDirectory(os.path.dirname(file_path))
        out = open(fullpath, 'wb')
        out.write(bytes(stream.read()))
        out.close()
        return fullpath

    def openFile(self, file_path):
        self.logger.debug("Opening file <" + file_path + ">")
        fullpath = self.getFullPath(self.main_path, file_path)
        out = open(fullpath, 'rb')
        self.logger.debug("Opened, REMEMBER TO CLOSE IT")
        return out

    def closeFile(self, file_path, file):
        self.logger.debug("Closing file <" + file_path + ">")
        file.close()
        

    def renameFile(self, oldpath, newpath):
        self.logger.debug("Renaming file <" + oldpath + "> to <" + newpath + ">")
        fullpath_old = self.getFullPath(self.main_path, oldpath)
        fullpath_new = self.getFullPath(self.main_path, newpath)
        os.rename(fullpath_old,fullpath_new)
        return True


    def remove(self, path):
        fullpath = self.getFullPath(self.main_path, path)
        self.logger.debug("Removing file/folder <" + fullpath + ">")
        if os.path.isdir(fullpath):
            self.__removeRecursive(fullpath)
        elif os.path.isfile(fullpath):
            self.__removeFile(fullpath)
        else:
            self.logger.debug("Path <" + fullpath + "> doesn't exist. Not removing")

    def __removeFile(self, path):
        self.logger.debug("Removing file <" + path + ">")
        os.remove(path)

    def __removeRecursive(self, path):
        self.logger.debug("Removing folder <" + path + ">")
        import shutil
        shutil.rmtree(path)

    def getFullPath(self, path=None, name=None):
        self.logger.debug("GetFullPath Path = <" + str(path) + ">, Name = <" + str(name) + ">")
        if path is None:
            path = self.main_path
        elif not os.path.isabs(path):
            path = os.path.join(self.main_path, path)

        finalpath = path
        if name is not None:
            name = os.path.normpath(name)
            finalpath = os.path.join(path, name)
            if os.path.isabs(finalpath):
                commonpref = os.path.commonprefix([self.main_path, finalpath])
                if self.main_path is not commonpref:
                    if commonpref:
                        finalpath = finalpath.split(commonpref, 1)[-1]
                    else:
                        finalpath = finalpath.split(os.sep, 1)[-1]
                    finalpath = os.path.join(path, finalpath)
            path = finalpath

        self.logger.debug("FullPath = <" + str(path) + ">")
        return os.path.abspath(path)

    def getHomeDir(self):
        return os.path.expanduser("~")

    def getFileList(self):
        self.logger.info('getFileList')
        fileList = []
        for root, dirnames, filenames in os.walk(self.main_path):
            for filename in filenames:
                filePath = os.path.normpath(root + '/' + filename)
                filePath = filePath.split(os.path.commonprefix([filePath, self.main_path]), 1)[-1]
                if os.sep == '\\':
                    filePath = filePath.replace('\\', '/')
                self.logger.debug('listing file <' + filePath + '>')
                fileList.append(filePath)

        self.logger.debug('fileList = <' + str(fileList) + '>')
        return fileList

    def md5sum(self, filename):
        filename = self.getFullPath(self.main_path,filename)
        with open(filename, mode='rb') as f:
            d = hashlib.md5()
            for buf in iter(partial(f.read, 128), b''):
                d.update(buf)
        return d.hexdigest()

