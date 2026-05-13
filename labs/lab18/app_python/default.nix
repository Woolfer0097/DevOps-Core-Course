{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    prometheus-client
    uvicorn
  ]);
in
pkgs.stdenvNoCC.mkDerivation rec {
  pname = "devops-info-service";
  version = "1.0.0";

  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        base = builtins.baseNameOf path;
      in
        !(base == "result"
          || base == "venv"
          || base == ".venv"
          || base == "__pycache__"
          || base == ".pytest_cache"
          || pkgs.lib.hasSuffix ".pyc" base);
  };

  dontBuild = true;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/${pname} $out/bin
    cp app.py $out/share/${pname}/app.py

    makeWrapper ${pythonEnv}/bin/uvicorn $out/bin/devops-info-service \
      --chdir $out/share/${pname} \
      --set-default HOST 0.0.0.0 \
      --set-default PORT 5000 \
      --set-default DATA_DIR /tmp/devops-info-service-data \
      --set-default CONFIG_FILE /tmp/devops-info-service-config.json \
      --add-flags "app:app --host 0.0.0.0 --port 5000"

    runHook postInstall
  '';

  meta = {
    description = "FastAPI DevOps information service built reproducibly with Nix";
    mainProgram = "devops-info-service";
  };
}
