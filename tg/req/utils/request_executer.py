# from typing import AnyStr, List, Union, NewType

import json


class RequestExecuter:
    def __init__(self, **kwargs) -> None:
        for key in kwargs:
            setattr(self, key, kwargs[key])


    def __repr__(self) -> str:
        attrs = []
        
        for attr in self.__dict__:
            attrs.append(
                f'{attr}={getattr(self, attr)}'
            )

        return f'{self.__class__.__name__}({",".join(attrs)})'
    

    def __getattr__(self, attr) -> Exception:
        raise Exception(f'Cant find {attr} in object {self}')


    async def execute(self, *args, **kwargs):
        request_type = self.request.method.lower()
        params = None
        
        if request_type == 'post':
            try:
                if self.request.FILES:
                    params = {
                        'type': 'json',
                        'data': {},
                    }
                
                else:
                    params = {
                        'type': 'json',
                        'data': json.loads(self.request.body) if getattr(self.request, 'body') else {},
                    }
            
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                params  = {
                    'type': 'str',
                    'data': str(getattr(self.request, 'body') or ''),
                }
            
        elif request_type == 'get':
            params = {
                'type': 'json',
                'data': getattr(self.request, 'GET').dict(),
            }
        
        elif request_type == 'delete':
            try:
                params = {
                    'type': 'json',
                    'data': json.loads(self.request.body) if getattr(self.request, 'body') else {},
                }
            
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                params  = {
                    'type': 'str',
                    'data': str(getattr(self.request, 'body') or ''),
                }
        
        return await getattr(self, request_type)(params = params, *args, **kwargs)


if __name__ == '__main__':
    class Test:
        method = 'GET'

    def ex(req):
        print(req)

    t = Test()
    reqexe = RequestExecuter(t, post = ex)

    reqexe.execute()