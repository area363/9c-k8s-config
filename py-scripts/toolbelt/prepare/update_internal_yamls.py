import yaml

import toolbelt.client.github as github
from toolbelt.planet.apv import Planet

planet = Planet()


def update_internal_yamls(
    version: str, timestamp: str, properties: dict, apv=None
) -> str:
    assert version.startswith("v"), f"{version}"

    branch_name = f"{version}"

    repo_name = "9c-k8s-config"
    github.create_branch(repo_name, "main", branch_name)

    new_apv_str = apv
    for filepath in [
        "9c-internal/kustomization.yaml",
        "9c-internal/configmap-versions.yaml",
    ]:
        sha, content = github.get_path_content(repo_name, filepath, branch_name)
        doc = yaml.safe_load(content)

        if "kustomization" in filepath:
            for image in doc["images"]:
                if image["name"] == "kustomization-libplanet-seed":
                    _, tag = properties["libplanet.Seed"].docker_image.split(":")
                elif image["name"] == "kustomization-ninechronicles-headless":
                    _, tag = properties["NineChronicles.Headless"].docker_image.split(
                        ":"
                    )
                elif image["name"] == "kustomization-ninechronicles-snapshot":
                    _, tag = properties["NineChronicles.Snapshot"].docker_image.split(
                        ":"
                    )
                else:
                    raise Exception("Unknown image name: {}".format(image["name"]))
                image["newTag"] = tag
        elif "configmap-versions" in filepath:
            if not new_apv_str:
                internal_old_apv = planet.analyze_apv(
                    doc["data"]["APP_PROTOCOL_VERSION"]
                )
                print(f"Old APV: {internal_old_apv.raw}")
                internal_new_apv = planet.sign_apv(
                    "internal", internal_old_apv.version + 1, timestamp
                )
                print(f"New APV: {internal_new_apv.raw}")
                new_apv_str = internal_new_apv.raw

            doc["data"]["APP_PROTOCOL_VERSION"] = new_apv_str
        else:
            raise Exception("Unknown file name: {}".format(filepath))

        new_content = yaml.safe_dump(doc)
        if content != new_content:
            message = f"update {filepath}"
            github.update_path_content(
                repo_name, filepath, message, new_content, sha, branch_name
            )

    assert new_apv_str, "Failed to create new APV"
    return new_apv_str
