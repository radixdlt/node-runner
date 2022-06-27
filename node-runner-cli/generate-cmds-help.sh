filename="command_reference.adoc"
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

declare -a dockersubcommands=("configure" "config" "setup" "start" "stop")
for subcommand in "${dockersubcommands[@]}"
do
  command_help_doc "docker" "$subcommand" "$filename"
done

declare -a systemdsubcommands=("configure" "setup" "restart" "stop")
for subcommand in "${systemdsubcommands[@]}"
do
  command_help_doc "systemd" "$subcommand" "$filename"
done

declare -a authcommands=("set-admin-password" "set-superadmin-password" "set-metrics-password")
for subcommand in "${authcommands[@]}"
do
  command_help_doc "auth" "$subcommand" "$filename"
done

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


declare -a monitoringcommands=("config" "setup" "start" "stop")
for subcommand in "${monitoringcommands[@]}"
do
  command_help_doc "monitoring" "$subcommand" "$filename"
done
