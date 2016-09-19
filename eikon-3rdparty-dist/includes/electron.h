///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Electron 3rd Party Main Header file

#pragma warning( push )
#pragma warning( disable : 4623 )
#pragma warning( disable : 4201) // warning C4201: nonstandard extension used : nameless struct/union	uv.h
#pragma warning( disable : 4127) // warning C4127: conditional expression is constant
#pragma warning( disable : 4506) // warning C4506: no definition for inline function 'v8::Persistent<v8::Object> v8::Persistent<v8::Object>::New(v8::Handle<v8::Object>)'
#include <nan.h>
#pragma warning (pop)