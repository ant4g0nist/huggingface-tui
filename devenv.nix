{ pkgs, config, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "Hello from HuggingTui";

  packages = [
    # A native dependency of numpy
    pkgs.zlib

    # A python dependency outside of poetry.
    config.languages.python.package.pkgs.pjsua2
  ];

  languages.python = {
    enable = true;
    poetry.enable = true;
  };
}