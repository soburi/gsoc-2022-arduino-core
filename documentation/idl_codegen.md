# Arduino IDL Codegen Manual

This document explains how to use `protoc-gen-arduinoif` with the Arduino IDL `.proto` files in `idl/proto`.

## Goal

Generate C++ headers from proto service definitions with explicit control over:

1. `Ifc` class (pure virtual, virtual-source methods only)
2. `Api` class (delegate wrapper)
3. `Service` class (pure virtual service contract)
4. `ServiceImpl` class (service implementation delegating to `Api`)

The generator supports per-method and per-service options in `arduino_opts.proto`.

## Files

1. Generator: `alt_core_api/tools/protoc-gen-arduinoif`
2. Options: `alt_core_api/idl/proto/arduino_opts.proto`
3. IDL services: `alt_core_api/idl/proto/*.proto`

## Build Integration

`alt_core_api/idl/CMakeLists.txt` already invokes the plugin and emits headers into the build tree.
The build also generates `arduino_opts_pb2.py` and passes its path via `PROTOC_GEN_ARDUINOIF_PB2`.
The plugin requires this environment variable and does not generate pb2 at runtime.

## Processing Model

The generator uses a three-stage pipeline:

1. Build `RequestContext` from `CodeGeneratorRequest` (`message_map`, `service_index`, requested file sets, lineage cache).
2. Build `ServiceModel` IR per service from descriptors, options, lineage, and method specs.
3. Stream render headers from each model in order: `ifc -> api -> service -> service_impl`.

`ServiceModel` stores methods as a single list with per-surface flags (`in_ifc`, `in_api`, `in_service`, `in_service_impl`) to avoid duplicating method collections.

Only `RequestContext` is global. Service models are built and emitted one-by-one.

Module visibility is intentionally constrained:

1. `request_context.py` exposes `RequestContext`.
2. `service_model.py` exposes the `ServiceModel` data structure.
3. `service_model_builder.py` exposes `ServiceModelBuilder` as the model-construction entry point.
4. `service_renderer.py` exposes `ServiceRenderer` for header rendering.

Typical generated header names (per service):

1. `*_interface.hpp`
2. `*_api.hpp`
3. `*_service.hpp`
4. `*_service_impl.hpp`

## Method Options

Defined in `alt_core_api/idl/proto/arduino_opts.proto` as `google.protobuf.MethodOptions` extensions:

1. `cpp_name`
2. `cpp_return`
3. `cpp_arg_types`
4. `source_virtual`
5. `emit_api`
6. `emit_service`
7. `method_visibility`

### Meaning

1. `cpp_name`
   C++ method name. If omitted, RPC name is used.
2. `cpp_return`
   C++ return type override. If omitted, output message is inferred (`0 field -> void`, `1 field -> field type`, otherwise `void`).
3. `cpp_arg_types`
   Optional repeated list of C++ argument types. If present, these types are used with auto names (`arg0`, `arg1`, ...), and input message fields are ignored for arguments.
4. `source_virtual`
   Marks whether this method is considered virtual in the source Arduino class model.
5. `emit_api`
   Whether this method is emitted to generated `Api`.
6. `emit_service`
   Whether this method is emitted to generated `Service`.
7. `method_visibility`
   Access specifier for generated methods. Supported values: `public`, `protected`, `private` (default: `public`).

## Service Options

Defined as `google.protobuf.ServiceOptions` extensions:

1. `generate_ifc_class`
2. `generate_api_class`
3. `generate_service_class`
4. `generate_service_impl_class`
5. `ifc_class_name`
6. `api_class_name`
7. `service_class_name`
8. `service_impl_class_name`
9. `api_member_name`
10. `base_services`

### Meaning

1. `generate_ifc_class`
   Emit `<ServiceName>Ifc` (or overridden class name).
2. `generate_api_class`
   Emit `<ServiceName>Api` delegate wrapper.
3. `generate_service_class`
   Emit `<ServiceName>Service` pure virtual class.
4. `generate_service_impl_class`
   Emit `<ServiceName>ServiceImpl` delegating to `Api`.
5. `*_class_name`
   Override generated class names.
6. `api_member_name`
   Override delegate member name in `ServiceImpl` (default: `api_`).
7. `base_services`
   Parent services to inherit from. You can specify a same-package short name (for example `Print`) or a fully-qualified name (for example `arduino.idl.Print` or `.arduino.idl.Print`). Generated `Service` class declarations inherit all ancestor `Ifc` classes (direct and indirect) in lineage order.

## Recommended Mapping

Use this mapping for mixed virtual/non-virtual Arduino APIs:

1. `Ifc`
   Include only methods with `source_virtual = true`.
2. `Api`
   Wrapper for `Ifc` operations.
3. `Service`
   Contract surface for service exposure. You can include additional methods via `emit_service = true`.
4. `ServiceImpl`
   Delegates service calls into an `Api` object.

## Validation Rules (Fail Fast)

The generator intentionally fails when configuration is inconsistent:

1. `generate_api_class = true` requires `generate_ifc_class = true`
2. `generate_service_impl_class = true` requires `generate_service_class = true`
3. `generate_api_class = true` rejects methods with `emit_api = true` and `source_virtual = false`
4. `generate_service_impl_class = true` with `generate_api_class = true` requires all `Service` methods to be callable on generated `Api`
5. Cyclic `base_services` references are rejected
6. If `base_services` is set and `generate_service_class = true`, each ancestor service must also set `generate_ifc_class = true`

## Example

```proto
syntax = "proto3";
package arduino.idl;

import "arduino_opts.proto";
import "google/protobuf/empty.proto";

service Demo {
  option (arduino.generate_ifc_class) = true;
  option (arduino.generate_api_class) = true;
  option (arduino.generate_service_class) = true;
  option (arduino.generate_service_impl_class) = true;

  option (arduino.ifc_class_name) = "DemoIfcCustom";
  option (arduino.api_class_name) = "DemoApiCustom";
  option (arduino.service_class_name) = "DemoServiceCustom";
  option (arduino.service_impl_class_name) = "DemoServiceImplCustom";
  option (arduino.api_member_name) = "delegate_";
  option (arduino.base_services) = "Print";

  rpc Read(google.protobuf.Empty) returns (google.protobuf.Empty) {
    option (arduino.cpp_name) = "read";
    option (arduino.cpp_return) = "int";
    option (arduino.source_virtual) = true;
    option (arduino.emit_api) = true;
    option (arduino.emit_service) = true;
    option (arduino.method_visibility) = "public";
  }
}
```

## Command Line Example

```sh
export PROTOC_GEN_ARDUINOIF_PB2=/path/to/arduino_opts_pb2.py
protoc \
  --plugin=protoc-gen-arduinoif=tools/protoc-gen-arduinoif \
  --arduinoif_out=/tmp/arduinoif-gen \
  --proto_path=idl/proto \
  --proto_path=idl/proto/google/protobuf \
  idl/proto/print.proto
```

## Notes

1. This generator produces headers only.
2. Runtime transport (for example nanopb framing, dispatch loop, registry) is a separate layer.
3. Keep API compatibility decisions in proto options so codegen output remains deterministic.
