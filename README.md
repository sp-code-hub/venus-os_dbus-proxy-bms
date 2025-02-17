# dbus-proxy-bms

Copy or rename the `config.sample.ini` to `config.ini` in the `dbus-proxy-bms` folder and change it as you need it.


## Install / Update

1. Login to your Venus OS device via SSH. See [Venus OS:Root Access](https://www.victronenergy.com/live/ccgx:root_access#root_access) for more details.
2. Execute this commands to download and copy the files:

    ```bash

    wget -O /tmp/download_dbus-proxy-bms.sh https://raw.githubusercontent.com/sp-code-hub/venus-os_dbus-proxy-bms/master/download.sh

    bash /tmp/download_dbus-proxy-bms.sh

    ```
3. Select the version you want to install.
4. Press enter for a single instance. For multiple instances, enter a number and press enter.

    Example:

   - Pressing enter or entering `1` will install the driver to `/data/etc/dbus-proxy-bms`.
   - Entering `2` will install the driver to `/data/etc/dbus-proxy-bms-2`.

### Extra steps for your first installation

5. Edit the config file to fit your needs. The correct command for your installation is shown after the installation.

   - If you pressed enter or entered `1` during installation:

    ```bash

    nano /data/etc/dbus-proxy-bms/config.ini

    ```

   - If you entered `2` during installation:

    ```bash

    nano /data/etc/dbus-proxy-bms-2/config.ini

    ```
6. Install the driver as a service. The correct command for your installation is shown after the installation.

   - If you pressed enter or entered `1` during installation:

    ```bash

    bash /data/etc/dbus-proxy-bms/install.sh

    ```

   - If you entered `2` during installation:

    ```bash

    bash /data/etc/dbus-proxy-bms-2/install.sh

    ```

    The daemon-tools should start this service automatically within seconds.

## Uninstall

⚠️ If you have multiple instances, ensure you choose the correct one. For example:

- To uninstall the default instance:

    ```bash

    bash /data/etc/dbus-proxy-bms/uninstall.sh

    ```
- To uninstall the second instance:

    ```bash

    bash /data/etc/dbus-proxy-bms-2/uninstall.sh

    ```

## Restart

⚠️ If you have multiple instances, ensure you choose the correct one. For example:

- To restart the default instance:

    ```bash

    bash /data/etc/dbus-proxy-bms/restart.sh

    ```
- To restart the second instance:

    ```bash

    bash /data/etc/dbus-proxy-bms-2/restart.sh

    ```

## Debugging

⚠️ If you have multiple instances, ensure you choose the correct one.

- To check the logs of the default instance:

    ```bash

    tail -n 100 -F /data/log/dbus-proxy-bms/current | tai64nlocal

    ```
- To check the logs of the second instance:

    ```bash

    tail -n 100 -F /data/log/dbus-proxy-bms-2/current | tai64nlocal

    ```

The service status can be checked with svstat `svstat /service/dbus-proxy-bms`

This will output somethink like `/service/dbus-proxy-bms: up (pid 5845) 185 seconds`

If the seconds are under 5 then the service crashes and gets restarted all the time. If you do not see anything in the logs you can increase the log level in `/data/etc/dbus-proxy-bms/dbus-proxy-bms.py` by changing `level=logging.WARNING` to `level=logging.INFO` or `level=logging.DEBUG`

If the script stops with the message `dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.battery.proxy_bms"` it means that the service is still running or another service is using that bus name.
