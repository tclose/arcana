# Arcana XNAT Plugin #

This is a plugin to provide datatypes required by the Arcana package
(https://github.com/monashbiomedicalimaging/arcana). 


# Building #

To build the Arcana XNAT plugin:

1. If you haven't already, clone this repository and cd to the newly cloned folder.
1. Build the plugin: `./gradlew jar` (on Windows, you can use the batch file: `gradlew.bat jar`).
This should build the plugin in the file **build/libs/xnat-workshop-plugin-1.0.0.jar** (the
version may differ based on updates to the code).
1. Copy the plugin jar to your plugins folder:
`cp build/libs/xnat-workshop-plugin-1.0.0.jar /data/xnat/home/plugins`

# Deploying #

Deploying the plugin just requires copying it to the **plugins** folder for your XNAT installation.
The location of the **plugins** folder varies based on how and where you have installed your XNAT.

You can also set up a share for your Vagrant configuration that actually creates the VM's **plugins**
folder as a share with your host machine. This allows you to deploy the plugin by copying it into the
shared local folder, where it will then appear on the VM in the linked shared folder.

Once you've copied the plugin jar into your XNAT's **plugins** folder, you need to restart the Tomcat
server. Your new plugin will be available as soon as the restart and initialization process is
completed.

