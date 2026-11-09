import 'package:flet/flet.dart';
import 'keystore_control.dart';

CreateControlFactory createControl = (CreateControlArgs args) {
  if (args.control.type != 'botkingkeystore') return null;
  return KeystoreControl(
    parent: args.parent,
    control: args.control,
    nextChild: args.nextChild,
    backend: args.backend,
  );
};

void ensureInitialized() {}
