# Calamus MO Supplement — W105

W105 Menu and UI-State Decoupling is built from published W104 baseline `92aa832c6b72cb7a81a5a44c656890ec602d9d41`.

Accepted architecture: a GTK-free declarative application `MenuModel`, immutable `UiStateSnapshot`, one `UiStateController` that derives command availability and visual projection from the same snapshot, and one GTK `MenuGtkAdapter` as sole global application-menu projector. Global check/sensitivity state is logical data; widgets are never authoritative state. Dynamic application-menu families are immutable row projections. Panel runtimes no longer receive menu widgets; appearance/opacity/line-number gateways no longer reach through to menu controls.

W104 stable command identity remains authoritative. W106 Preferences/Application State Extraction and W107 Subsystem Host-Port Migration remain explicitly deferred.

Permanent desktop validation authority remains: cryptographic Candidate/launcher identity + synchronous `EXIT=0`, `ERR=NONE`, `FINAL_PHASE=RUNNER_RETURNED_PASS`, plus explicit human PASS.
