filename="../docs/command_reference.adoc"
command_help_doc()
{
  #$1 allsubcommand
  #$2 subcommand
  #$3 filename
  echo $1 $2 $3
  echo "" >> $3
	echo "=== $1 $2" >> $3
	echo "[source, bash]" >> $3
	echo "----" >> $3
	./radixnode.py $1 $2 -h >> $3
	echo "----" >> $3
}

command_api_help_doc()
{
  #$1 allsubcommand
  #$2 subcommand
  #$3 filename
  echo $1 $2 $3
	echo "=== $1 $2" >> $3
	echo "[source, bash]" >> $3
	echo "----" >> $3
	./radixnode.py "api" $1 $2 -h >> $3
	echo "----" >> $3
}

echo "" > "$filename"

cat <<EOT >> "$filename"
=== Core node or Gateway setup using docker
Below are the list of commands that can be used with cli to setup a core node or gateway.
EOT

declare -a dockersubcommands=("configure" "config" "setup" "start" "stop")
for subcommand in "${dockersubcommands[@]}"
do
  command_help_doc "docker" "$subcommand" "$filename"
done


cat <<EOT >> "$filename"
=== Radix node CLI command reference
This document is to list all the commands and features that radixnode CLI supports.
EOT
declare -a systemdsubcommands=("configure" "setup" "restart" "stop")
for subcommand in "${systemdsubcommands[@]}"
do
  command_help_doc "systemd" "$subcommand" "$filename"
done

cat <<EOT >> "$filename"
=== Set passwords for the Nginx server
This will set up the admin user and password for access to the general system endpoints.
EOT
declare -a authcommands=("set-admin-password" "set-superadmin-password" "set-metrics-password")
for subcommand in "${authcommands[@]}"
do
  command_help_doc "auth" "$subcommand" "$filename"
done

cat <<EOT >> "$filename"
=== Accessing core endpoints using CLI
Once the nginx basic auth passwords for admin, superadmin, metrics users are setup , radixnode cli can be used to access the node endpoints
EOT
declare -a coreapicommands=("entity" "key-list" "mempool" "mempool-transaction" "update-validator-config")
for subcommand in "${coreapicommands[@]}"
do
  command_api_help_doc "core" "$subcommand" "$filename"
done


declare -a systemapicommands=("metrics" "health" "version")
for subcommand in "${systemapicommands[@]}"
do
  command_api_help_doc "system" "$subcommand" "$filename"
done


cat <<EOT >> "$filename"
=== Setup monitoring using CLI
Using CLI , one can setup monitoring of the node or gateway.
EOT
declare -a monitoringcommands=("config" "setup" "start" "stop")
for subcommand in "${monitoringcommands[@]}"
do
  command_help_doc "monitoring" "$subcommand" "$filename"
done
