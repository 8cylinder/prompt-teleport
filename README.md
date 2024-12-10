

### Dir teleport

``` bash
function cdd
{
    eval "$(python3 $HOME/bin/cd-projects.py cd "$1")"
}
# completion for cdd
function _cdd
{
    # the sed removes blank lines and lines starting with a comment (#)
    local cur=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=(
        $(compgen -W \
          "$(sed "/\(^$\|^#\)/d" < $HOME/.sink-projects | cut -f1 | sort | xargs)" -- "$cur")
    )
}
complete -F _cdd cdd
```

### Prompt

``` bash
# load the bash prompt source
function _prompt_command() {
    export PS1="$($HOME/bin/bashrc_prompt.py)"
}
export PROMPT_COMMAND=_prompt_command
```

### UI

prompt ps1
prompt themes
prompt project cd [DIR-NAME]
prompt project add NAME PROJECT-ROOT [COLOUR]
prompt project edit
