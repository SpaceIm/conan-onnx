from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
import textwrap

required_conan_version = ">=1.33.0"


class OnnxConan(ConanFile):
    name = "onnx"
    description = "Open standard for machine learning interoperability."
    license = "Apache-2.0"
    topics = ("conan", "onnx", "machine-learning", "deep-learning", "neural-network")
    homepage = "https://github.com/onnx/onnx"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    exports_sources = "CMakeLists.txt"
    generators = "cmake", "cmake_find_package"
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def requirements(self):
        self.requires("protobuf/3.13.0")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["ONNX_BUILD_BENCHMARKS"] = False
        self._cmake.definitions["ONNX_USE_PROTOBUF_SHARED_LIBS"] = self.options["protobuf"].shared
        self._cmake.definitions["BUILD_ONNX_PYTHON"] = False
        self._cmake.definitions["ONNX_GEN_PB_TYPE_STUBS"] = False
        self._cmake.definitions["ONNX_WERROR"] = False
        self._cmake.definitions["ONNX_COVERAGE"] = False
        self._cmake.definitions["ONNX_BUILD_TESTS"] = False
        self._cmake.definitions["ONNX_USE_LITE_PROTO"] = False
        self._cmake.definitions["ONNXIFI_ENABLE_EXT"] = False
        self._cmake.definitions["ONNX_ML"] = True
        self._cmake.definitions["ONNXIFI_DUMMY_BACKEND"] = False
        self._cmake.definitions["ONNX_VERIFY_PROTO3"] = tools.Version(self.deps_cpp_info["protobuf"].version).major == "3"
        if self.settings.compiler.get_safe("runtime"):
            self._cmake.definitions["ONNX_USE_MSVC_STATIC_RUNTIME"] = str(self.settings.compiler.runtime) in ["MT", "MTd", "static"]
        self._cmake.configure()
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path),
            {
                "onnx_proto": "ONNX::onnx_proto",
                "onnx": "ONNX::onnx",
            }
        )

    @staticmethod
    def _create_cmake_module_alias_targets(module_file, targets):
        content = ""
        for alias, aliased in targets.items():
            content += textwrap.dedent("""\
                if(TARGET {aliased} AND NOT TARGET {alias})
                    add_library({alias} INTERFACE IMPORTED)
                    set_property(TARGET {alias} PROPERTY INTERFACE_LINK_LIBRARIES {aliased})
                endif()
            """.format(alias=alias, aliased=aliased))
        tools.save(module_file, content)

    @property
    def _module_subfolder(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(self._module_subfolder,
                            "conan-official-{}-targets.cmake".format(self.name))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "ONNX"
        self.cpp_info.names["cmake_find_package_multi"] = "ONNX"


        self.cpp_info.components["onnx_proto"].names["cmake_find_package"] = "onnx_proto"
        self.cpp_info.components["onnx_proto"].names["cmake_find_package_multi"] = "onnx_proto"
        self.cpp_info.components["onnx_proto"].builddirs.append(self._module_subfolder)
        self.cpp_info.components["onnx_proto"].build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.components["onnx_proto"].build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
        self.cpp_info.components["onnx_proto"].libs = ["onnx_proto"]
        self.cpp_info.components["onnx_proto"].defines = ["ONNX_NAMESPACE=onnx", "ONNX_ML=1"]
        self.cpp_info.components["onnx_proto"].requires = ["protobuf::libprotobuf"]

        self.cpp_info.components["libonnx"].names["cmake_find_package"] = "onnx"
        self.cpp_info.components["libonnx"].names["cmake_find_package_multi"] = "onnx"
        self.cpp_info.components["libonnx"].builddirs.append(self._module_subfolder)
        self.cpp_info.components["libonnx"].build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.components["libonnx"].build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
        self.cpp_info.components["libonnx"].libs = ["onnx"]
        self.cpp_info.components["libonnx"].defines = ["ONNX_NAMESPACE=onnx", "ONNX_ML=1"]
        self.cpp_info.components["libonnx"].requires = ["onnx_proto"]

        # TODO: add targets like onnxifi, onnxifi_dummy, onnxifi_loader and onnxifi_wrapper?
