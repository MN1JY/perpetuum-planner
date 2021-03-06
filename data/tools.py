"""Collection of command line tools for working with Perpetuum data."""

import argparse
from collections import defaultdict
from perpetuum import *


def command_data(args):
    """GBF file operations"""

    data = DataFile(args.input)
    try:
        os.makedirs(args.output)
    except OSError:
        pass
    data.dump_records(args.names or ['*'], args.output, args.sort)


def command_skin(args):
    """Skin file operations"""

    try:
        os.makedirs(args.output)
    except OSError:
        pass

    from PyQt4 import QtCore, QtGui
    app = QtGui.QApplication([]) # needed to access fonts

    skin = SkinFile(args.input)

    for image in skin.images:
        with open(os.path.join(args.output, 'image_%04d.png' % image.id), 'wb') as f:
            f.write(image.data)

        qimage = QtGui.QImage()
        qimage.loadFromData(image.data, 'PNG')

        for rect in skin.rects:
            if rect.image_id == image.id:
                qrect = QtCore.QRect(rect.x1, rect.y1, rect.x2 - rect.x1, rect.y2 - rect.y1)
                if args.parts:
                    part_filename = os.path.join(args.output, 'part_%04d_%04d.png' % (rect.id, rect.image_id))
                    qimage.copy(qrect).save(part_filename, 'PNG')

        painter = QtGui.QPainter(qimage)
        font = QtGui.QFont('Arial Narrow')
        font.setPixelSize(8)
        font.setStyleStrategy(QtGui.QFont.NoAntialias)
        painter.setFont(font)

        for rect in skin.rects:
            if rect.image_id == image.id:
                qrect = QtCore.QRect(rect.x1, rect.y1, rect.x2 - rect.x1, rect.y2 - rect.y1)
                painter.setPen(QtCore.Qt.red)
                painter.drawRect(qrect)
                painter.setPen(QtCore.Qt.green)
                painter.drawText(rect.x1, rect.y1 + 6, unicode(rect.id))

        painter.end()
        qimage.save(QtCore.QFile(os.path.join(args.output, 'parts_%04d.png' % image.id)), 'PNG')

    with open(os.path.join(args.output, 'dict.txt'), 'wb') as f:
        f.write(skin.dict)


def command_convert(args):
    with open(args.input, 'rb') as f:
        data = f.read()

    if args.format == 'xml':
        from lxml import etree
        data = etree.tostring(genxy_parse(data, 'xml'),
                              xml_declaration=True,
                              encoding='UTF-8',
                              pretty_print=True)
        ext = 'xml'
    elif args.format == 'yaml':
        import yaml
        import yaml_use_ordered_dict
        data = yaml.dump(genxy_parse(data))
        ext = 'yaml'

    with open(args.output, 'wb') as f:
        f.write(data)


def main():
    parser = argparse.ArgumentParser(description='Perpetuum data utilities.')
    subparsers = parser.add_subparsers(help='Available commands')

    subparser = subparsers.add_parser('data', help='Dump content from Perpetuum.gbf.')
    subparser.add_argument('-i', '--input', metavar='PATH', required=True, help='Input file path')
    subparser.add_argument('-o', '--output', metavar='PATH', default='.', help='Output directory')
    subparser.add_argument('-n', '--name', dest='names', action='append', metavar='NAMES',
                           help='Record name to extract. Can be used multiple times. Glob patterns are supported.')
    subparser.add_argument('--sort', action='store_true', default=False,
                           help='Create subfolders and sort extracted files by category.')
    subparser.set_defaults(command=command_data)

    subparser = subparsers.add_parser('skin', help='Parse skin file.')
    subparser.add_argument('-i', '--input', metavar='PATH', required=True, help='Input file path')
    subparser.add_argument('-o', '--output', metavar='PATH', default='.', help='Output directory')
    subparser.add_argument('--parts', action='store_true', help='Save slices as separate images')
    subparser.set_defaults(command=command_skin)

    subparser = subparsers.add_parser('convert', help='Convert genxy files to various formats.')
    subparser.add_argument('-i', '--input', metavar='PATH', required=True, help='Input file path')
    subparser.add_argument('-o', '--output', metavar='PATH', required=True, help='Output file path')
    subparser.add_argument('-f', '--format', choices=['xml', 'yaml'], default='raw', help='Output format')
    subparser.set_defaults(command=command_convert)

    args = parser.parse_args()
    args.command(args)


if __name__ == '__main__':
    main()
