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
    tsg.vm.synced_folder data_dir,     "/home/vagrant/" + data_dir, disabled: false
    tsg.vm.synced_folder etc_dir,      "/home/vagrant/" + etc_dir, disabled: false

    tsg.vm.provider "virtualbox" do |vb|
      vb.gui = false
      vb.memory = 4096

      # Allow the creation of symlinks for nvm
      vb.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant","1"]
    end


    tsg.vm.provision "pkg-update", type: "shell", run: "once",
                            privileged: true, inline: <<-SHELL
        apt-get update
        apt-get install -y net-tools git libmagic1
    SHELL

    tsg.vm.provision "python-env", type: "shell", run: "once",
                            privileged: true, inline: <<-SHELL
        apt-get install -y python3-dev python3-pip
        apt-get install -y libcurl4-openssl-dev libssl-dev
        apt-get install -y cmake libsm6 libxrender1 libxext6 \
                  libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon-x11-0 libxdamage1 libxcomposite-dev \
                  libxrandr2 libgbm-dev libpangocairo-1.0-0
        pip3 install pytest
        pip3 install neo4j==1.7.6
        pip3 install numpy pandas unidecode nltk pyyaml dumper
        pip3 install jinja2
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
        pip3 install detools python-magic
        pip3 install pymango dnspython
        SHELL

    tsg.vm.provision "configure-pythonpath", type: "shell", env: {"PYTHONPATH"=>ENV['PYTHONPATH']}, inline: <<-SHELL
        echo "export PYTHONPATH=$PYTHONPATH:/home/vagrant/binstore" >> /home/vagrant/.bash_profile
    SHELL

  end

end
