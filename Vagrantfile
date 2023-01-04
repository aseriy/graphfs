# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'fileutils'

download_dir  = 'Download'
binstore_dir  = 'binstore'
data_dir      = 'Data'
etc_dir       = 'etc'

class VagrantPlugins::ProviderVirtualBox::Action::Network
  def dhcp_server_matches_config?(dhcp_server, config)
    true
  end
end

Vagrant.configure("2") do |config|

  config.trigger.before :up do
    Dir.mkdir(download_dir) unless File.exist?(download_dir)
    Dir.mkdir(dataset_dir) unless File.exist?(binstore_dir)
    Dir.mkdir(etc_dir) unless File.exist?(etc_dir)
  end

  config.vm.define "tsg" do |tsg|
    tsg.vm.box = "bento/ubuntu-20.04"

    tsg.vm.network "private_network", type: "dhcp"

    tsg.vm.synced_folder ".", "/vagrant", disabled: true
    tsg.vm.synced_folder download_dir, "/home/vagrant/" + download_dir, disabled: false
    tsg.vm.synced_folder binstore_dir, "/home/vagrant/" + binstore_dir, disabled: false
    tsg.vm.synced_folder data_dir, "/home/vagrant/" + data_dir, disabled: false
    tsg.vm.synced_folder etc_dir, "/home/vagrant/" + etc_dir, disabled: false

    tsg.vm.provider "virtualbox" do |vb|
      vb.gui = false
      vb.memory = 4096

      # Allow the creation of symlinks for nvm
      vb.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant","1"]
    end

    tsg.vm.provision "java8", type: "shell", run: "once",
                        args: [download_dir], privileged: true, inline: <<-SHELL
        DOWNLOAD_DIR=$1
        cd /opt
        if [ -d jdk1.8.0_231 ]
        then
          rm -fr jdk1.8.0_231
        fi
        tar xzf /home/vagrant/${DOWNLOAD_DIR}/jdk-8u231-linux-x64.tar.gz
        ln -s jdk1.8.0_231 jdk
        chown -R root.root jdk1.8.0_231
    SHELL

    tsg.vm.provision "neo4j", type: "shell", run: "once",
                        args: [download_dir], privileged: true, inline: <<-SHELL
        DOWNLOAD_DIR=$1
        NEO4J_HOME=neo4j-community-3.5.13
        cd /opt
        if [ -d ${NEO4J_HOME} ]
        then
          rm -fr ${NEO4J_HOME}
        fi
        tar xzf /home/vagrant/${DOWNLOAD_DIR}/${NEO4J_HOME}-unix.tar.gz
        if [ ! -d ${NEO4J_HOME}/plugins ]
        then
            mkdir ${NEO4J_HOME}/plugins
        fi
        cp /home/vagrant/${1}/apoc-3.5.0.4-all.jar ${NEO4J_HOME}/plugins
        cp /home/vagrant/${1}/neo4j-graphql-3.5.0.4.jar ${NEO4J_HOME}/plugins
        ln -s ${NEO4J_HOME} neo4j
        grep '^neo4j\:' /etc/passwd > /dev/null 2>&1
        if [ $? -ne 0 ]
        then
            adduser --system --group neo4j --shell /bin/bash
        fi
        chown -R neo4j.neo4j ${NEO4J_HOME}
    SHELL

    tsg.vm.provision "neo4j-plugins", type: "shell", run: "once",
                        privileged: true, inline: <<-SHELL
        NEO4J_HOME=neo4j-community-3.5.13
        cd /opt/${NEO4J_HOME}/plugins
        wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/3.5.0.4/apoc-3.5.0.4-all.jar
        wget https://github.com/neo4j-graphql/neo4j-graphql/releases/download/3.5.0.4/neo4j-graphql-3.5.0.4.jar
        chown neo4j:neo4j *.jar
    SHELL

    tsg.vm.provision "pkg-update", type: "shell", run: "once",
                            privileged: true, inline: <<-SHELL
        apt-get update
        apt-get install -y net-tools git
    SHELL

    tsg.vm.provision "python-env", type: "shell", run: "once",
                            privileged: true, inline: <<-SHELL
        apt-get install -y python3-dev python3-pip
        apt-get install -y libcurl4-openssl-dev libssl-dev
        apt-get install -y cmake libsm6 libxrender1 libxext6
        pip3 install pytest
        pip3 install neo4j==1.7.6
        pip3 install numpy pandas unidecode nltk pyyaml dumper
        pip3 install Keras tensorflow
        pip3 install jinja2
        pip3 install boto3
        pip3 install numpy
        pip3 install pandas
        pip3 install more_itertools
        pip3 install Dumper
        pip3 install wptools
        pip3 install requests
        pip3 install geopy
        pip3 install aiohttp
        pip3 install --upgrade chardet
        pip3 install matplotlib
        pip3 install --upgrade requests
        SHELL

    tsg.vm.provision "configure-pythonpath", type: "shell", env: {"PYTHONPATH"=>ENV['PYTHONPATH']}, inline: <<-SHELL
        echo "export PYTHONPATH=$PYTHONPATH:/home/vagrant/binstore" >> /home/vagrant/.bash_profile
    SHELL

    tsg.vm.provision "ulimit", type: "shell", privileged: true,
                            run: "once", inline: <<-SHELL
        echo "*    soft nofile 64000" >> /etc/security/limits.conf
        echo "*    hard nofile 64000" >> /etc/security/limits.conf
        echo "root soft nofile 64000" >> /etc/security/limits.conf
        echo "root hard nofile 64000" >> /etc/security/limits.conf
        echo "session required pam_limits.so" >> /etc/pam.d/common-session
        echo "session required pam_limits.so" >> /etc/pam.d/common-session-noninteractive
    SHELL

    tsg.vm.provision "docker", type: "shell", run: "once",
                            privileged: true, inline: <<-SHELL
        apt-get update
        apt-get -y install \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg-agent \
            software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

        add-apt-repository \
           "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
           $(lsb_release -cs) \
           stable"
        apt-get update
        add-apt-repository \
             "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
             disco \
             stable"
        apt-get -y install docker-ce docker-ce-cli containerd.io
     SHELL

    tsg.vm.provision "neo4j-run", type: "shell", run: "never",
                        args: [etc_dir], privileged: true, inline: <<-SHELL
        if [ -f /home/vagrant/${1}/neo4j.ip ]; then
          rm -f /home/vagrant/${1}/neo4j.ip
        fi
        hostname -I | awk '{print $2}' > /home/vagrant/${1}/neo4j.ip
        chown vagrant.vagrant /home/vagrant/${1}/neo4j.ip

        cd /opt/neo4j
        HOST_IP=`cat /home/vagrant/${1}/neo4j.ip`
        CONF_FILE=conf/neo4j.conf
        if [ -f "${CONF_FILE}.bak" ]; then
          mv ${CONF_FILE}.bak ${CONF_FILE}
        fi
        cp $CONF_FILE ${CONF_FILE}.bak
        echo >> $CONF_FILE
        echo "dbms.connectors.default_listen_address=${HOST_IP}" >> $CONF_FILE
        echo "dbms.connector.bolt.listen_address=${HOST_IP}:7687" >> $CONF_FILE
        echo "dbms.connector.http.listen_address=${HOST_IP}:7474" >> $CONF_FILE
        chown -R neo4j.neo4j .
        STATUS=`su -s /bin/bash -c 'cd /opt/neo4j; JAVA_HOME=/opt/jdk bin/neo4j status' neo4j`
        if [ "$STATUS" = "Neo4j is not running" ];then
          su -s /bin/bash -c 'cd /opt/neo4j; JAVA_HOME=/opt/jdk bin/neo4j start' neo4j
        else
          su -s /bin/bash -c 'cd /opt/neo4j; JAVA_HOME=/opt/jdk bin/neo4j restart' neo4j
        fi
        su -s /bin/bash -c 'cd /opt/neo4j; JAVA_HOME=/opt/jdk bin/neo4j status' neo4j

        # chown vagrant.vagrant /home/vagrant/${1}/config.yml
#         sed -i 's/'local_uri'/'#'/' /home/vagrant/${1}/config.yml
#     echo -e 'local_uri: '${HOST_IP} >> /home/vagrant/${1}/config.yml

    SHELL

    tsg.vm.provision "neo4j-password", type: "shell", run: "never",
                        args: [etc_dir], privileged: true, inline: <<-SHELL
        HOST_IP=`cat /home/vagrant/${1}/neo4j.ip`

        curl --location --request POST http://neo4j:neo4j@${HOST_IP}:7474/user/neo4j/password \
          --header 'Accept: application/json; charset=UTF-8' \
          --header 'Content-Type: application/json' \
          --data-raw '{"password" : "binstore"}'
    SHELL

  end

end
