Vagrant.configure("2") do |config|
config.vm.box = "ubuntu/trusty64"
  config.vm.box_url = "https://vagrantcloud.com/ubuntu/boxes/trusty64"
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
    v.cpus = 2
  end
  config.vm.network :forwarded_port, guest: 8000, host: 8000, auto_correct: true
# Uncomment line below if you want localhost access to postgres; do not do this on production!
# config.vm.network :forwarded_port, guest: 5432, host: 5432, auto_correct: true
  config.vm.provision :shell, :path => "vagrant/bootstrap.sh"
  config.vm.synced_folder ".", "/vagrant", :mount_options => ["dmode=777","fmode=666"]
end