{
  description = "DevOps Info Service - reproducible Nix build";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      app = import ./default.nix { inherit pkgs; };
    in
    {
      packages.${system} = {
        default = app;
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      apps.${system}.default = {
        type = "app";
        program = "${app}/bin/devops-info-service";
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (pkgs.python3.withPackages (ps: with ps; [
            fastapi
            prometheus-client
            uvicorn
          ]))
        ];
      };
    };
}
