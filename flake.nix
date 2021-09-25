{
  description = "Collection of experimental utility scripts for Tracking The Trackers project.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix-src.url = "github:DavHau/mach-nix";
    #axml2xml-src = {
    #  url = "github:ngi/apkparser";
    #};
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src }:
    let
      lib = nixpkgs.lib;
      defaultSystems = flake-utils.lib.defaultSystems;
      buildSystems = lib.lists.subtractLists
        [ "aarch64-darwin" "x86_64-darwin" ] defaultSystems;
    in
      flake-utils.lib.eachDefaultSystem (
        system:
          let
            pkgs = import nixpkgs { inherit system; };

            mach-nix = import mach-nix-src { inherit pkgs; python = "python38"; };

            pyEnv = mach-nix.mkPython rec {
              requirements = ''
                requests
                github3.py
                xmltodict
                pyasn
                appdirs
                pyyaml
                androguard
              '';
            };
          in
            {
              # defaultPackage = self.packages.${system}.${pname};
              packages = { inherit pkgs; };
              devShell = mach-nix.nixpkgs.mkShell {
                # TODO add axml2xml go package as buildInput
                buildInputs = with pkgs; [ pyEnv fdroidserver jdk11_headless wget curl ];
              };
            }
      );
}
