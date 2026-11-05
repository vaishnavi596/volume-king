"""Compare actual same-contract broker snapshots, never infer investor intent."""
import math

def changes(current, previous, epoch_matches=True):
    valid = (epoch_matches and previous.get('symbol') == current.get('symbol')
             and previous.get('expiry') == current.get('expiry')
             and current.get('source') == previous.get('source') == 'Angel One')
    old={(r.get('strike'),r.get('side')):r for r in previous.get('rows',[])} if valid else {}
    result=[]
    for original in current.get('rows',[]):
        row=dict(original);before=old.get((row.get('strike'),row.get('side')), {})
        t, prior=row.get('timestamp'),before.get('timestamp')
        if (isinstance(t,(int,float)) and isinstance(prior,(int,float))
                and 0 < t-prior <= 3600):
            for field in ('oi','premium'):
                x,y=row.get(field),before.get(field)
                if all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in (x,y)):
                    row[field+'_change']=x-y
            row['change_since']=prior
        result.append(row)
    return result
