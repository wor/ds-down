ds-down
=======

ds-down is a Python program to send URLs and local files to Synology
DownloadStation using aforementioned DownloadStations Web API (`API pdf`_).

The main intended use-case is from console and a desktop file for xdg-open or
similar tools is provided.

Example config_ file:

.. code-block:: ini

    # Example config file, by default it should be located at:
    # ~/.config/ds-down.conf

    username     = admin
    host         = https://192.168.1.10:5001
    passwordeval = gpg --no-tty -d ~/.passwords/synology-admin.gpg

Examples
--------

Send a magnet link to the DownloadStation:

.. code-block:: bash

    $ ds-down 'magnet:?xt=urn:btih:dbd7d976a5bf566504357bf9f543a37d3513e4df&dn=archlinux-2014.07.03-dual.iso&tr=udp://tracker.archlinux.org:6969&tr=http://tracker.archlinux.org:6969/announce'

Send a locally stored torrent file to the DownloadStation:

.. code-block:: bash

    $ ds-down 'archlinux-2014.07.03-dual.iso.torrent'


.. _`API pdf`: http://ukdl.synology.com/download/Document/DeveloperGuide/Synology_Download_Station_Web_API.pdf
.. _config: https://github.com/wor/ds-down/
